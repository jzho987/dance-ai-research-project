package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/jzho987/dance-ai-research-project/src/bailandopp/test_client/test_generate_dance_sequence"
	"github.com/jzho987/dance-ai-research-project/src/bailandopp/test_client/test_send_music"
)

func main() {
	musicFile := os.Args[1]
	inputFile := os.Args[2]
	outputFile := os.Args[3]
	REQUEST_LENGTH := 200
	REQUEST_SHIFT := 28
	err := test_send_music.SendMusicRequest(&musicFile, "single")
	if err != nil {
		print("failed to send music")
		panic(err)
	}

	fmt.Printf("handling sending %s. \n", inputFile)
	file, err := os.ReadFile(inputFile)
	if err != nil {
		print("failed to read file")
		panic(err)
	}
	result := make([][]float32, 0)
	err = json.Unmarshal(file, &result)
	if err != nil {
		print("failed to unmarshal")
		panic(err)
	}
	QueryAndWriteToJson(REQUEST_LENGTH, REQUEST_SHIFT, result, outputFile)

	fmt.Println("WENT!")
}

func QueryAndWriteToJson(requestLength int, requestShift int, input [][]float32, outFileName string) {

	response, err := test_generate_dance_sequence.Generate_dance_sequence_request(requestLength, requestShift, input, "music", 0)
	if err != nil {
		fmt.Println("failed to generate dance sequence")
		panic(err)
	}
	data, err := json.Marshal(response)
	if err != nil {
		fmt.Println("failed to marshal response")
		panic(err)
	}
	// Write JSON string to file
	err = os.WriteFile(outFileName, data, 0644)
	if err != nil {
		fmt.Println("failed to write to file")
		panic(err)
	}
}
