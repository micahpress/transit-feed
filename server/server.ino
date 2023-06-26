#include "dependencies/credentials.h"
#include <WiFiNINA.h>
#include <LiquidCrystal_I2C.h>
#include <string>
#include <WiFi.h>

using namespace std;

char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
int status = WL_IDLE_STATUS;
int LCD_COLS = 20;
int LCD_ROWS = 4;
int scrollOffset = LCD_COLS - 1;
WiFiServer server(80);

LiquidCrystal_I2C lcd(0x27,LCD_COLS,LCD_ROWS);

void setup() {
  Serial.begin(9600);
  lcd.init();
  lcd.backlight();
  while (status != WL_CONNECTED) {
    printMessage("Attempting to connect to network: " + string(ssid), 0);
    // Connect to WPA/WPA2 network:
    status = WiFi.begin(ssid, pass);

    // wait 3 seconds for connection:
    delay(3000);
  }
  lcd.clear();
  IPAddress ip = WiFi.localIP();
  printMessage("Connected with IP:", 0);
  printIp(ip, 1);
  delay(3000);
  server.begin();
}

void loop() {
  WiFiClient client = server.available();

    if (client) {                             // if you get a client,
    Serial.println("new client");           // print a message out the serial port
    string currentLine = "";                // make a String to hold incoming data from the client

    while (client.connected()) {            // loop while the client's connected
      if (client.available()) {             // if there's bytes to read from the client,
        char c = client.read();             // read a byte, then
        Serial.write(c);                    // print it out the serial monitor

        if (c == '\n') {                    // if the byte is a newline character
          // if the current line is blank, you got two newline characters in a row.
          // that's the end of the client HTTP request, so send a response:
          if (currentLine.length() == 0) {
            lcd.clear();
            int row = 0;
            char bodyC;
            while (client.available()) {
              bodyC = client.read();
              if (bodyC == '\n') {
                printMessage(currentLine, row);
                currentLine = "";
                row++;
              } else {
                currentLine += bodyC;
              }
            }

            // HTTP headers always start with a response code (e.g. HTTP/1.1 200 OK)
            // and a content-type so the client knows what's coming, then a blank line:
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            client.println();
            // The HTTP response ends with another blank line:
            client.println();
            // break out of the while loop:
            break;
          } else {    // if you got a newline, then clear currentLine:
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }
      }
    }
    // close the connection:
    client.stop();
    Serial.println("client disconnected");
  }
}

void printIp(IPAddress ip, int row) {
  lcd.setCursor(0, row);
  lcd.print(ip);
}

void printMessage(string message, int row) {
  while (row < LCD_ROWS && message.size() > LCD_COLS) {
    lcd.setCursor(0, row);
    lcd.print(message.substr(0, LCD_COLS).c_str());
    Serial.println(message.substr(0, LCD_COLS).c_str());
    message = message.substr(LCD_COLS, message.size());
    row++;
  }
  lcd.setCursor(0, row);
  lcd.print(message.c_str());
  Serial.println(message.c_str());
}
