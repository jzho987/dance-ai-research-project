package test_send_music

import (
	"bytes"
	"crypto/tls"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
)

type music_payload struct {
	MusicID string `json:"musicID"`
	Payload string `json:"payload"`
}

func SendMusicRequest(fileName *string, musicID string) error {
	url := "http://localhost:8000/music"

	name := "../data/chill_music.wav"
	if fileName != nil {
		name = *fileName
	}
	fmt.Printf("use music: %s \n", name)
	file, err := os.ReadFile(name)
	if err != nil {
		print("failed to read file")
		return err
	}
	payloadString := base64.StdEncoding.EncodeToString(file)
	payload := music_payload{
		MusicID: musicID,
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

	_, err = io.ReadAll(response.Body)
	if err != nil {
		print("failed to read all")
		return err
	}

	return nil
}
