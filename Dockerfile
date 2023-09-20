# Goland version: 1.20.5-alpine
FROM golang:1.20.5-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy the local package files to the container's workspace
COPY . .

# Install Python3 and create a symlink to Python
RUN apk --no-cache add python3
RUN apk --no-cache add py3-pip

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Build the Go application inside the container
RUN go build -o api

# Expose the port that your HTTP server will run on
EXPOSE 1111

# Command to run your application
CMD ["./api","1111"]
