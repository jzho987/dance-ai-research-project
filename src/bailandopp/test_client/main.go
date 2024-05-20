package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/jzho987/dance-ai-research-project/src/bailandopp/test_client/test_generate_dance_sequence"
	"github.com/jzho987/dance-ai-research-project/src/bailandopp/test_client/test_send_music"
)

const REQUEST_LENGTH = 100
const REQUEST_SHIFT = 2

func main() {
	err := test_send_music.Send_music_request()
	if err != nil {
		print("failed to send music")
		panic(err)
	}

	response, err := test_generate_dance_sequence.Generate_dance_sequence_request(REQUEST_LENGTH, REQUEST_SHIFT)
	if err != nil {
		print("failed to generate dance sequence")
		panic(err)
	}

	data, err := json.Marshal(response)
	if err != nil {
		print("failed to marshal response")
		panic(err)
	}

	// Write JSON string to file
	err = os.WriteFile("result.json", data, 0644)
	if err != nil {
		print("failed to write to file")
		panic(err)
	}

	fmt.Printf("goed! received %d action frames.", len(response.Result))
}
