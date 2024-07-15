package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/jzho987/dance-ai-research-project/src/bailandopp/test_client/test_generate_dance_sequence"
	"github.com/jzho987/dance-ai-research-project/src/bailandopp/test_client/test_send_music"
)

const REQUEST_LENGTH = 100
const REQUEST_SHIFT = 28
const TOTAL = 12

func main() {
	GENERATE_MUSIC := strings.Split(os.Args[1], ".")[0]
	fileName := fmt.Sprintf("./data/music/%s.wav", GENERATE_MUSIC)
	err := test_send_music.SendMusicRequest(&fileName, GENERATE_MUSIC)
	if err != nil {
		print("failed to send music")
		panic(err)
	}
	return

	sourceDir := "./data/motion/"
	resultDir := "./result/"
	for i := 0; i <= TOTAL; i++ {
		fullPath := fmt.Sprintf("%spregen_%d.json", sourceDir, i)
		fmt.Printf("handling sending %s", fullPath)
		outPath := fmt.Sprintf("%s%s_generated_%d_shift_%d.json", resultDir, GENERATE_MUSIC, i, REQUEST_SHIFT)
		file, err := os.ReadFile(fullPath)
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
		QueryAndWriteToJson(REQUEST_LENGTH, REQUEST_SHIFT, result, outPath, GENERATE_MUSIC)
	}

	print("goed!!!")
}

func QueryAndWriteToJson(requestLength int, requestShift int, payload [][]float32, outFileName string, musicName string) {

	response, err := test_generate_dance_sequence.Generate_dance_sequence_request(REQUEST_LENGTH, REQUEST_SHIFT, payload, musicName, 0)
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
