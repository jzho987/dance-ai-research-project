package main

import (
	"bytes"
	"crypto/tls"
	"encoding/base64"
	"encoding/json"
	"io"
	"net/http"
	"os"
)

type music_payload struct {
	MusicID string `json:"musicID"`
	Payload string `json:"payload"`
}

func main() {
	url := "http://localhost:8000/music"

	file, err := os.ReadFile("../data/mBR0.wav")
	if err != nil {
		print("failed to read file")
		panic(err)
	}
	payloadString := base64.StdEncoding.EncodeToString(file)
	payload := music_payload{
		MusicID: "music_id",
		Payload: payloadString,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		print("failed to marshal json")
		panic(err)
	}

	sendMusicRequest, err := http.NewRequest("POST", url, bytes.NewBuffer(data))
	if err != nil {
		print("failed to create http request")
		panic(err)
	}
	sendMusicRequest.Header.Set("Content-type", "application/json")

	tls_config := tls.Config{
		InsecureSkipVerify: true,
	}
	tr := &http.Transport{
		TLSClientConfig: &tls_config,
	}
	client := &http.Client{Transport: tr}
	response, err := client.Do(sendMusicRequest)
	if err != nil {
		print("failed to do http request")
		panic(err)
	}

	data, err = io.ReadAll(response.Body)
	if err != nil {
		print("failed to read all")
		panic(err)
	}
	println(response.Status)
	println(string(data))
}
