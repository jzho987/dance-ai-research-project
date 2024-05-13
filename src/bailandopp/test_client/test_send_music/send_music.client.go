package test_send_music

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

func Send_music_request() error {
	url := "http://localhost:8000/music"

	file, err := os.ReadFile("data/mBR0.wav")
	if err != nil {
		print("failed to read file")
		return err
	}
	payloadString := base64.StdEncoding.EncodeToString(file)
	payload := music_payload{
		MusicID: "music_id",
		Payload: payloadString,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		print("failed to marshal json")
		return err
	}

	sendMusicRequest, err := http.NewRequest("POST", url, bytes.NewBuffer(data))
	if err != nil {
		print("failed to create http request")
		return err
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
		return err
	}

	data, err = io.ReadAll(response.Body)
	if err != nil {
		print("failed to read all")
		return err
	}

	return nil
}
