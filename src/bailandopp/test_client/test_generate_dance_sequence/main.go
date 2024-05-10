package main

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"io"
	"net/http"
	"os"
)

type generate_payload struct {
	MusicID         string      `json:"musicID"`
	StartFrameIndex int         `json:"startFrameIndex"`
	Length          int         `json:"length"`
	Payload         [][]float32 `json:"payload"`
}

type result_payload struct {
	Dance [][]float32 `json:"dance"`
}

func main() {
	url := "http://localhost:8000/dance-sequence"

	file, err := os.ReadFile("../../app/data/dance_data.json")
	if err != nil {
		print("failed to read file")
		panic(err)
	}
	var result [][]float32
	err = json.Unmarshal(file, &result)
	if err != nil {
		print("failed to unmarshal")
		panic(err)
	}
	payload := generate_payload{
		MusicID:         "music_id",
		Length:          20,
		StartFrameIndex: 10,
		Payload:         result,
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
	resultPayload := result_payload{}
	err = json.Unmarshal(data, &resultPayload)
	if err != nil {
		print("failed to unmarshal result")
		panic(err)
	}

	println(response.Status)
	println(len(resultPayload.Dance))
}
