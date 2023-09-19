#




## Running
sudo docker build -t simple-html-server -f Dockerfile-html_file_server .
sudo docker run -d -p 8888:80 -v ./performance_tests:/usr/share/nginx/html --name file-server simple-html-server
### stop
sudo docker stop file-server
### remove
sudo docker rm file-server
