package main

import (
	"crypto/rand"
	"encoding/json"
	"fmt"
	"math/big"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"
)



var (
	serverURL 		string
	concurrentRequests int
	runDuration        time.Duration
	testUniqueName     string
	outputFolder       string
	testDisplayName    string
	testDescription    string
	testStartTime      int64
)

type MetaData struct {
	ServerURL 		string  `json:"server_url"`
	TestUniqueName     string  `json:"test_unique_name"`
	TestDisplayName    string  `json:"test_display_name"`
	TestDescription    string  `json:"test_description"`
	Folder             string  `json:"folder"`
	ConcurrentRequests int     `json:"concurrent_requests"`
	TestDuration       int     `json:"test_duration"`
	TotalRequests      int     `json:"total_requests"`
	SuccessfulRequests int     `json:"successful_requests"`
	FailedRequests     int     `json:"failed_requests"`
	RequestsPerSecond  float64 `json:"requests_per_second"`
	TestStartTime	  int64  `json:"test_start_time"`
}

type ResponseData struct {
	IP             string `json:"ip"`
	LookupDuration int64  `json:"lookupDuration"`
	Occurences     int    `json:"occurences"`
}

type StatData struct {
	IP              string `json:"ip"`
	Occurences      int    `json:"occurences"`
	LookupDuration  int64  `json:"lookupDuration"`
	RequestDuration int64  `json:"requestDuration"`
	StartTime       int64  `json:"startTime"`
	EndTime         int64  `json:"endTime"`
}

func TestPerformance(t *testing.T) {

	// Parse command-line arguments and set global variables.
	if len(os.Args) != 9 {
		fmt.Println("Usage: go test -args <concurrent_requests> <duration_seconds> <test_unique_name> <test_display_name> <test_description> <endpoint_url>")
		return
	}

	// Ensure the "performance_tests" directory exists else create it.
	performanceTestsDir := "performance_tests"
	if _, err := os.Stat(performanceTestsDir); os.IsNotExist(err) {
		os.Mkdir(performanceTestsDir, 0777)
	}

	// Parse command-line arguments.
	concurrentRequests = parseArg(3)

	runDuration = time.Duration(parseArg(4)) * time.Second

	testUniqueName = os.Args[5]
	// replace spaces with underscores
	testUniqueName = strings.ReplaceAll(testUniqueName, " ", "_")
	outputFolder = performanceTestsDir + "/" + testUniqueName + "/"
	// Ensure the output directory exists else create it.
	if _, err := os.Stat(outputFolder); os.IsNotExist(err) {
		os.Mkdir(outputFolder, 0777)
	}

	testDisplayName = os.Args[6]

	testDescription = os.Args[7]

	serverURL = os.Args[8]

	testStartTime = time.Now().UnixNano()

	// Record test metrics.
	var (
		wg             sync.WaitGroup
		latencyResults []time.Duration
		failedRequests int
		mu             sync.Mutex
	)

	startTime := time.Now()
	endTime := startTime.Add(runDuration)
	var statData []StatData
	for i := 0; i < concurrentRequests; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			// Set the "IP_ADR" header with the random IP.
			client := &http.Client{}

			for time.Now().Before(endTime) {
				req, err := http.NewRequest("GET", serverURL, nil)
				if err != nil {
					t.Errorf("Error creating request: %v", err)
					return
				}
				// Generate a random IP address.
				// intentionally generate a random IP address for each request
				ip := generateRandomIP()

				// Using an arbitrary header key to store the IP address.
				// This is unnecessary since the IP address is already in the request.
				// However, this is done to simulate a real-world scenario where a large number of users are sending requests.
				req.Header.Add("IP_ADR", ip)

				// Record the start time.
				startTime := time.Now()

				// Send the request.
				resp, err := client.Do(req)
				if err != nil {
					t.Errorf("Error sending request: %v", err)
					// Increment the failed requests count.
					mu.Lock()
					failedRequests++
					mu.Unlock()
					continue
				}
				latency := time.Since(startTime)
				var responseData ResponseData
				if err := json.NewDecoder(resp.Body).Decode(&responseData); err != nil {
					t.Errorf("Error decoding response: %v", err)
					return
				}

				// Create a stat data item.
				var statDataItem StatData = StatData{
					IP:              responseData.IP,
					Occurences:      responseData.Occurences,
					LookupDuration:  responseData.LookupDuration,
					RequestDuration: latency.Nanoseconds(),
					StartTime:       startTime.UnixNano(),
					EndTime:         endTime.UnixNano(),
				}

				// Append the stat data item to the stat data slice.
				mu.Lock()
				statData = append(statData, statDataItem)
				mu.Unlock()
				resp.Body.Close()

				// Append the latency to the latency results slice.
				mu.Lock()
				latencyResults = append(latencyResults, latency)
				mu.Unlock()
			}
		}()
	}

	// Wait for the specified duration.
	time.Sleep(runDuration)

	// Write metadata to the output file.
	if err := writeMetaDataToFile(testDescription, latencyResults, failedRequests); err != nil {
		t.Errorf("Error writing metadata to file!: %v", err)
		return
	}

	// Write stat data to the output file.
	if err := writeRawDataToFile(statData); err != nil {
		t.Errorf("Error writing stat data to file!: %v", err)
		return
	}

	// Call the Python script to create graphs.
	if err := callPythonScript(); err != nil {
		t.Errorf("Error calling Python script: %v", err)
	}
}

func parseArg(index int) int {
	arg := os.Args[index]
	val, err := strconv.Atoi(arg)
	if err != nil {
		panic(fmt.Sprintf("Invalid argument: %s", arg))
	}
	return val
}

func generateRandomIP() string {
	// Generate a random IP address in the form "xxx.xxx.xxx.xxx"
	ip := make(net.IP, 4)

	for i := 0; i < 4; i++ {
		bigInt, err := rand.Int(rand.Reader, big.NewInt(256))
		if err != nil {
			panic(err)
		}
		ip[i] = byte(bigInt.Int64())
	}
	return ip.String()

	// old
	//ip := make([]byte, 4)
	//rand.Read(ip)
	//return fmt.Sprintf("%d.%d.%d.%d", ip[0], ip[1], ip[2], ip[3])
}

func writeRawDataToFile(statData []StatData) error {
	// write to csv file

	fmt.Printf("Directory path: %s\n", outputFolder)

	fmt.Printf("File path: %s\n", outputFolder+"data.csv")
	// write CSV Header
	csvFile, err := os.Create(outputFolder + "data.csv")
	if err != nil {
		fmt.Println(err)
	}
	defer csvFile.Close()

	// write CSV records
	for _, statDataItem := range statData {
		//fmt.Println(statDataItem)
		_, err := csvFile.WriteString(fmt.Sprintf("%s,%d,%d,%d,%d,%d\n", statDataItem.IP, statDataItem.Occurences, statDataItem.LookupDuration, statDataItem.RequestDuration, statDataItem.StartTime, statDataItem.EndTime))
		if err != nil {
			fmt.Println(err)
		}
	}
	csvFile.Sync()
	return nil
}

func writeMetaDataToFile(metaData string, latencyResults []time.Duration, failedRequests int) error {
	var meta MetaData
	meta.ServerURL = serverURL
	meta.TestUniqueName = testUniqueName
	meta.TestDisplayName = testDisplayName
	meta.TestDescription = metaData
	meta.Folder = outputFolder
	meta.ConcurrentRequests = concurrentRequests
	meta.TestDuration = int(runDuration.Seconds())
	meta.TotalRequests = len(latencyResults) + failedRequests
	meta.SuccessfulRequests = meta.TotalRequests - failedRequests
	meta.FailedRequests = failedRequests
	meta.RequestsPerSecond = float64(meta.TotalRequests) / runDuration.Seconds()
	meta.TestStartTime = testStartTime

	jsonFile, err := os.Create(meta.Folder + "metadata.json")
	if err != nil {
		fmt.Println(err)
	}
	defer jsonFile.Close()

	jsonData, err := json.MarshalIndent(meta, "", "  ")
	if err != nil {
		return fmt.Errorf("Error marshaling meta to JSON: %v", err)
	}

	// Write the JSON data to the file.
	err = os.WriteFile(outputFolder+"metadata.json", jsonData, 0666)
	if err != nil {
		return fmt.Errorf("Error writing meta to file: %v", err)
	}

	return nil
}
func callPythonScript() error {
	// Generate report first
	pythonScriptPath := "generate_report.py"
	cmd := exec.Command("python", pythonScriptPath, testUniqueName)
	// Set the working directory to the directory containing the Python script.
	cmd.Dir = filepath.Dir(pythonScriptPath)

	// Run the Python script.
	err := cmd.Run()
	if err != nil {
		return err
	}

	// Reindex index.html
	pythonScriptPath = "reindex.py"
	cmd = exec.Command("python", pythonScriptPath)
	cmd.Dir = filepath.Dir(pythonScriptPath)
	err = cmd.Run()
	if err != nil {
		return err
	}



	return nil
}
