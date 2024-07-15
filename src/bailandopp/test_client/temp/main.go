package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/jzho987/dance-ai-research-project/src/bailandopp/test_client/test_generate_dance_sequence"
	"github.com/jzho987/dance-ai-research-project/src/bailandopp/test_client/test_send_music"
)

const REQUEST_LENGTH = 100
const REQUEST_SHIFT = 28
const SEED = 14
const GENERATE_MUSIC = "trimmed_ambient"
const TOTAL = 12

func main() {
	fileName := fmt.Sprintf("../data/%s.wav", GENERATE_MUSIC)
	err := test_send_music.SendMusicRequest(&fileName, GENERATE_MUSIC)
	if err != nil {
		print("failed to send music")
		panic(err)
	}

	sourceDir := "../data/motion/"
	checkDir := "../seed/"
	resultDir := "../result/"
	var lastEndRes [][]float32 = nil
	for i := 0; i <= TOTAL; i++ {
		fullPath := fmt.Sprintf("%spregen_%d.json", sourceDir, i)
		fmt.Printf("handling sending %s. \n", fullPath)
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
		sendPayload := make([][]float32, 0)
		if lastEndRes != nil {
			sendPayload = append(sendPayload, lastEndRes...)
			sendPayload = append(sendPayload, result[:SEED*8]...)
			data := fmt.Sprintf("%+v \n %+v", sendPayload[112:113], sendPayload[113:114])
			check_full_path := fmt.Sprintf("%sseed_%d.json", checkDir, i)
			err = os.WriteFile(check_full_path, []byte(data), 0644)
			if err != nil {
				fmt.Println("failed to write to file")
				panic(err)
			}
		} else {
			sendPayload = result
		}
		outPath := fmt.Sprintf("%s%s_seeded_%d_shift_%d.json", resultDir, GENERATE_MUSIC, i, REQUEST_SHIFT)
		lastEndRes = QueryAndWriteToJson(REQUEST_LENGTH, REQUEST_SHIFT, sendPayload, outPath)
	}

	print("goed!!!")
}

func QueryAndWriteToJson(requestLength int, requestShift int, input [][]float32, outFileName string) [][]float32 {

	response, err := test_generate_dance_sequence.Generate_dance_sequence_request(REQUEST_LENGTH, REQUEST_SHIFT, input, "music", 0)
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

	endPos := len(response.Result) - 1 - (28-SEED)*8
	endClip := response.Result[endPos:]
	return endClip
}
