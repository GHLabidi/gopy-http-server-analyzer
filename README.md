# GO-PY-HTTP-SERVER-ANALYZER
## Description
This project showcases a way to analyze the performance of a web server.
### The web server (main.go)
- The web server is written in Golang. It has a hash table that stores the ip of each request and how many times it has been requested.
- It first looks for the ip in the hash table, if it is not there it adds it, if it is there it increments the counter.
- The web server returns a json with the ip and the number of requests and how long it took to find the ip in the hash table.
### The tester (main_test.go)
- The tester is written in Golang. It continuously sends requests with random ip addresses to the web server.
- It records the total request time and the lookup time for each request.
- After all data is collected, it saves a data.csv and a metadata.json file.
- It then calls a python script to analyze the data.
- Lastly it calls reindex.py which creates an index.html file for an nginx server to serve all of the reports.
### The analyzer (generate_report.py)
- The analyzer generates a report.html file with the data collected by the tester.

## Sample reports
- [View Reports](https://gopy-reports.ghdevlab.com/)

## How to run
### Requirements
- Golang
- Python 3
    - pandas
    - numpy
    - plotly
- Docker
- Docker-compose
### Steps
- Clone the repository and cd into it
#### Option 1: Run directly on your machine
- Run `go build -o api` to build the web server
- Run `./api <PORT>` to start the web server
- Run `go test -args <concurrent_requests> <duration_seconds> <test_unique_name> <test_display_name> <test_description> <server_url>` to start the tester and generate the report
- All data will be saved in the performance_tests folder
#### Option 2: Run on docker
- Run `docker-compose up -d` to start the web server
- Use run_test_on_docker.sh to start the tester and generate the report
    - `chmod +x run_test_on_docker.sh` to make the script executable
    - Usage `./run_test_on_docker.sh <docker-container-name> <concurrent_requests> <duration_seconds> <test_unique_name> <test_display_name> <test_description> <server_url`
- All data will be saved in the performance_tests folder (binded volume)
#### (Optional) Run the nginx server
- Run `cd file_server`
- Run `docker-compose up -d`
- Go to http://localhost:8888 to see the reports

## TODOs
- [ ] Automate testing using jenkins
- [ ] Add more documentation

## Author
- [Ghassen Labidi](https://github.com/GHLabidi)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

