package test_generate_dance_sequence

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"io"
	"net/http"
)

type generate_payload struct {
	MusicID         string      `json:"musicID"`
	StartFrameIndex int         `json:"startFrameIndex"`
	Length          int         `json:"length"`
	Shift           int         `json:"shift"`
	Payload         [][]float32 `json:"payload"`
	Seed            int         `json:"seed"`
}

type Result_payload struct {
	Result [][]float32 `json:"result"`
	Quant  [][]float32 `json:"quant"`
}

func Generate_dance_sequence_request(length int, shift int, input [][]float32, musicName string, seed int) (*Result_payload, error) {
	url := "http://localhost:8000/dance-sequence"

	payload := generate_payload{
		MusicID:         musicName,
		Length:          length,
		Shift:           shift,
		StartFrameIndex: 0,
		Payload:         input,
		Seed:            seed,
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
