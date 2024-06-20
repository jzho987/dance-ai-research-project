package main

import (
	"fmt"
	"os"

	"github.com/jzho987/dance-ai-research-project/src/bailandopp/test_client/test_send_music"
)

func main() {
	musicFile := os.Args[1]
	musicFile = fmt.Sprintf("../data/music/%s", musicFile)
	err := test_send_music.SendMusicRequest(&musicFile, "music")
	if err != nil {
		print("failed to send music")
		panic(err)
	}
}
