import socket
import sys
import struct
import threading
import time
import json
from datetime import datetime
sys.path.append(r"C:\Users\kitmi\Downloads\pynaoqi-python2.7-2.8.6.23-win64-vs2015-20191127_152649\lib")
from naoqi import ALProxy

# NAO robot configuration

PORT = 9559

# Socket configuration
SERVER_IP = "127.0.0.1"
SERVER_PORT = 9999
COMMAND_PORT = 9998

def handle_commands(tts_proxy):

    command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    command_socket.bind((SERVER_IP, COMMAND_PORT))
    command_socket.listen(1)
    print("Command server listening on {}:{}".format(SERVER_IP, COMMAND_PORT))
    
    def speak_word(number):
        
        words = {
            1: "It seems like I'm having difficulty detecting you. Could you please try moving?",
            2: "Goodbye",
            3: "Yes, that is good exercise keep it",
            4: "No, dont lazy to do exercises and squatting properly",
            5: "I know u are ready, you can start squatting now",
            6: "Thank you",
            7: "Nice relaxing exercise, you can do more",
            8: "Nice squatting keep it",
            9: "Please standing properly, left shoulder is raised"
        }
        word = words.get(number, "Invalid number")
        tts_proxy.say(word)

    while True:  
        try:
            client_socket, client_address = command_socket.accept()
            print("Connection established with ", client_address)
            
            try:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break

                    try:
                        # Decode the data and attempt to convert to an integer
                        command_number = int(data.decode("utf-8"))
                        print("Received command: ", command_number)
                        speak_word(command_number)
                    except ValueError:
                        print("Invalid command received: ", data)
                        tts_proxy.say("Invalid command")

            except Exception as e:
                print("Error during command handling: ", e)
            finally:
                client_socket.close()
                print("Connection with ", client_address, "closed")
        
        except Exception as e:
            print("Error accepting connection: ", e)




def start_server(nao_ip):
    try:
        print("Connecting to NAO robot at", nao_ip)
        video_proxy = ALProxy("ALVideoDevice", nao_ip, PORT)
        tts_proxy = ALProxy("ALTextToSpeech", nao_ip, PORT)

        # Text you want the NAO robot to say
        # text_to_say = "Hello, I am NAO. How can I assist you today?"
        # tts_proxy.say(text_to_say)

        # Start command handling in a separate thread
        command_thread = threading.Thread(target=handle_commands, args=(tts_proxy,))
        command_thread.daemon = True
        command_thread.start()
        
        # Camera parameters
        camera_index = 0  # top camera = 0
        resolution = 2    # VGA (640x480)
        color_space = 13  # BGR
        fps = 30
        

        # Subscribe to the camera feed
        video_name = video_proxy.subscribeCamera(
            "python_client",
            camera_index,
            resolution,
            color_space,
            fps
        )
        
        # Set up video server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SERVER_IP, SERVER_PORT))
        server_socket.listen(1)
        print("Video server listening on {}:{}".format(SERVER_IP, SERVER_PORT))
        
        conn, addr = server_socket.accept()
        print("Video connection from:", addr)
        
        while True:
            # Capture frame from NAO camera
            nao_image = video_proxy.getImageRemote(video_name)
            if nao_image:
                width, height = nao_image[0], nao_image[1]
                raw_data = nao_image[6]
                
                conn.sendall(struct.pack('>I', width))
                conn.sendall(struct.pack('>I', height))
                conn.sendall(raw_data)
                
    except Exception as e:
        print("Error:", e)
        print("Please make sure the IP of the robot is correct")
        raise
    finally:
        # Cleanup
        if 'video_name' in locals():
            video_proxy.unsubscribe(video_name)
        if 'conn' in locals():
            conn.close()
        if 'server_socket' in locals():
            server_socket.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        nao_ip = sys.argv[1]
        start_server(nao_ip)
    else:
        print("Please provide the NAO robot IP address as a command line argument")
        sys.exit(1)