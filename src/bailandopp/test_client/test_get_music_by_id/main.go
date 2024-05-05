package main

import (
	"crypto/tls"
	"io"
	"net/http"
)

func main() {
	url := "http://localhost:8000/music/music_id-processed"

	getMusicByIDRequest, err := http.NewRequest("GET", url, nil)
	if err != nil {
		print("failed to create http request")
		panic(err)
	}
	getMusicByIDRequest.Header.Set("Content-type", "application/json")

	tls_config := tls.Config{
		InsecureSkipVerify: true,
	}
	tr := &http.Transport{
		TLSClientConfig: &tls_config,
	}
	client := &http.Client{Transport: tr}
	response, err := client.Do(getMusicByIDRequest)
	if err != nil {
		print("failed to do http request")
		panic(err)
	}

	data, err := io.ReadAll(response.Body)
	if err != nil {
		print("failed to read all")
		panic(err)
	}
	println(response.Status)
	println(string(data))
}
