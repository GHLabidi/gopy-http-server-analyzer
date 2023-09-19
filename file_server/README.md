# Simple File Server
## Description
Simple nginx file server to serve performance tests reports.
## Running
```sudo docker compose up -d```
## Stopping
```sudo docker compose down```
## Change performance tests directory
Change the volume in docker-compose.yml
```    
volumes:
      - <PATH_TO_PERFORMANCE_TESTS>:/usr/share/nginx/html
```