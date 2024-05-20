package test_generate_dance_sequence

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
	Shift           int         `json:"shift"`
	Payload         [][]float32 `json:"payload"`
}

type Result_payload struct {
	Result [][]float32 `json:"result"`
	Quant  [][]float32 `json:"quant"`
}

func Generate_dance_sequence_request(length int, shift int) (*Result_payload, error) {
	url := "http://localhost:8000/dance-sequence"

	file, err := os.ReadFile("../app/data/dance_data.json")
	if err != nil {
		print("failed to read file")
		return nil, err
	}
	var result [][]float32
	err = json.Unmarshal(file, &result)
	if err != nil {
		print("failed to unmarshal")
		return nil, err
	}
	payload := generate_payload{
		MusicID:         "music_id",
		Length:          length,
		Shift:           shift,
		StartFrameIndex: 0,
		Payload:         result,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		print("failed to marshal json")
		return nil, err
	}

	sendMusicRequest, err := http.NewRequest("POST", url, bytes.NewBuffer(data))
	if err != nil {
		print("failed to create http request")
		return nil, err
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
		return nil, err
	}

	data, err = io.ReadAll(response.Body)
	if err != nil {
		print("failed to read all")
		return nil, err
	}
	resultPayload := Result_payload{}
	err = json.Unmarshal(data, &resultPayload)
	if err != nil {
		print("failed to unmarshal result")
		return nil, err
	}

	return &resultPayload, nil
}
