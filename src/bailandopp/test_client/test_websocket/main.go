package main

import (
	"fmt"

	"golang.org/x/net/websocket"
)

func main() {
	ws, err := websocket.Dial("ws://localhost:8000/socket", "", "http://localhost:8000")
	if err != nil {
		print("failed to connect websocket")
		panic(err)
	}
	defer ws.Close()

	incomingMessages := make(chan string)
	go readClientMessages(ws, incomingMessages)
	send := true
	for {
		if !send {
			val, ok := <-incomingMessages
			if ok {
				println(val)
				send = true
			}
		} else {
			var input string
			print("enter message: ")
			fmt.Scanln(&input)
			if input != "" {
				websocket.Message.Send(ws, input)
				send = false
			}
		}
	}
}

func readClientMessages(ws *websocket.Conn, incomingMessages chan string) {
	for {
		var message string
		err := websocket.Message.Receive(ws, &message)
		if err != nil {
			fmt.Printf("Error::: %s\n", err.Error())
			return
		}
		incomingMessages <- message
	}
}
