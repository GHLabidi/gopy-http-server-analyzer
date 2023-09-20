package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"
	"os"
)

var (
	ips   map[string]int // Hash map to store IP addresses and their request counts
	mutex sync.Mutex
)

func main() {
	// get port from args
	port := os.Args[1]
	fmt.Println("Starting server on port " + port + "\n")
	// Initialize the hash map. Keys are IP addresses, values are request counts.
	ips = make(map[string]int)

	// /check_ip endpoint handler function.
	// This function looks up the IP address in the hash map. If the IP address is not in the map, add it else increment the count.
	http.HandleFunc("/check_ip", checkIP)

	// /stats endpoint handler function.
	// returns some stats about the hash map
	http.HandleFunc("/stats", returnHashMapStats)

	// /clear endpoint handler function.
	// clears the hash map
	http.HandleFunc("/clear", clearHashMap)

	// listen on port and if port is not available, exit with error
	err := http.ListenAndServe(":" + port, nil)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	
	
}

func checkIP(w http.ResponseWriter, r *http.Request) {
	mutex.Lock()
	defer mutex.Unlock()
	// Get the IP address from the "IP_ADR" header.
	// Ideally, this would be the IP address of the client making the request.
	ip := r.Header.Get("IP_ADR")

	lookupStart := time.Now()

	// Check if the IP address is in the map.
	if count, exists := ips[ip]; !exists {
		// If the IP is not in the map, it's a new request.
		ips[ip] = 1 // Initialize the count to 1.
		lookupDuration := time.Since(lookupStart)

		// Create a JSON response map.
		responseData := map[string]interface{}{
			"ip":             ip,
			"lookupDuration": lookupDuration.Nanoseconds(),
			"occurences":     0,
		}

		// Set the "Content-Type" header to "application/json."
		w.Header().Set("Content-Type", "application/json")

		// Encode the JSON and write it to the response writer.
		if err := json.NewEncoder(w).Encode(responseData); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	} else {
		// If the IP is in the map, it's a repeat request.
		ips[ip]++ // Increment the count.
		lookupDuration := time.Since(lookupStart)

		// Create a JSON response map.
		responseData := map[string]interface{}{
			"ip":             ip,
			"lookupDuration": lookupDuration.Nanoseconds(),
			"occurences":     count,
		}

		// Set the "Content-Type" header to "application/json."
		w.Header().Set("Content-Type", "application/json")

		// Encode the JSON and write it to the response writer.
		if err := json.NewEncoder(w).Encode(responseData); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	}
}

func returnHashMapStats(w http.ResponseWriter, r *http.Request) {
	mutex.Lock()
	defer mutex.Unlock()
	fmt.Fprintf(w, "IP Address Request Count\n")

	// most frequent ip and count
	mostFrequentIP := ""
	mostFrequentIPCount := 0

	for ip, count := range ips {
		if count > mostFrequentIPCount {
			mostFrequentIP = ip
			mostFrequentIPCount = count
		}
	}
	fmt.Fprintf(w, "Most Frequent IP: %s (%d)\n", mostFrequentIP, mostFrequentIPCount)
}

func clearHashMap(w http.ResponseWriter, r *http.Request) {
	mutex.Lock()
	defer mutex.Unlock()
	ips = make(map[string]int)
}
