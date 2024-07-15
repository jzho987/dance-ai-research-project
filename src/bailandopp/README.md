# Bailando

Bailandopp is a dance AI model created by Siyao et al. This directory refactors their original code and wraps it in a web server to expose the functionalities to our unity project.

## App

This is where the application server is. We use sanic to run the application server to host the AI agent for the clients to connect to.

### How to use

Make sure to first download all the requirements using the requirements.txt file, or manually download the requirements.
Then run this to start the sanic app.
```
sanic server
```
If you want the server to not just be on localhost, make sure to specify the host url
```
sanic server --host 0.0.0.0
```


## Test Clients

These are the golang clients that details the request and response regarding each endpoints in the AI agent server.

### How to use

Make sure you first download the correct version of golang.
Then run this to download dependencies.
```
go mod tidy
```
To run any of the clients, go to the folder where the main.go is, and run:
```
go run main.go <args>
```
The args are any command line argument that the script will need. Most does not have any, but some of the scripts will need the name of the music file as the first command line argument. Details see each scripts.

### NOTE
Some of the clients are not in the most up to date state. This should be updated before the repository is final.