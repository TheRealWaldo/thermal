/*
  This is an example sketch for Home Assisatnt Thermal integration.
  
  @Author: Eyal Cohen

  Pinouts
    MCU         Device
    D1          AMG SDA
    D2          AMG SCL
    D5          Led
*/

#include <Wire.h>
#include <Adafruit_AMG88xx.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoOTA.h>
#include <RemoteDebug.h>
#include <ArduinoJson.h>
#include <jled.h>

#include "secrets.h"

#define LED_RED D5

static RemoteDebug Debug;

static Adafruit_AMG88xx amg;
static float pixels[AMG88xx_PIXEL_ARRAY_SIZE];

static ESP8266WebServer server(80);

static const char* hostName = "grideye1";

auto ledRed = JLed(LED_RED);
auto ledBuiltin = JLed(BUILTIN_LED);

void wifiInit() {
  WiFi.mode(WIFI_STA);
  WiFi.hostname(hostName);
  WiFi.begin(ssid, password);
}

void wifiConnect() {
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

boolean otaInit() {
  ArduinoOTA.onStart([]() {
    Serial.println("Start");
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nEnd");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println("End Failed");
  });
  Serial.println("Start OTA");
  ArduinoOTA.begin();

  return true;
}

void handleRoot() {
  server.send(200, "text/plain", "hello from esp8266!");
}

void handleRaw() {
  String payload;
  float pixels[AMG88xx_PIXEL_ARRAY_SIZE];
  amg.readPixels(pixels);
  for (int i = 1; i <= AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    char pixel[10];
    dtostrf(pixels[i-1], 1, 2, pixel);
    payload += pixel;
    if (i < AMG88xx_PIXEL_ARRAY_SIZE) {
      payload += ',';
    }
  }
  StaticJsonDocument<512> doc;
  doc["sensor"] = "AMG8833";
  doc["rows"] = 8;
  doc["cols"] = 8;
  doc["data"] = payload.c_str();
  String output;
  serializeJson(doc, output);
  server.send(200, "application/json", output.c_str());
  ledRed.Blink(100, 100);
}

void handleNotFound() {
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";
  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  server.send(404, "text/plain", message);
}

boolean serverInit() {
  server.on("/", handleRoot);
  server.on("/raw", handleRaw);
  server.onNotFound(handleNotFound);
  server.begin();
}

void setup() {
  Serial.begin(115200);

  bool status;
  
  wifiInit();

  wifiConnect();
  serverInit();

  // default settings
  status = amg.begin();
  if (!status) {
    Serial.println("Could not find a valid AMG88xx sensor, check wiring!");
  }

  otaInit();

  Debug.begin(hostName);

  pinMode(LED_RED, OUTPUT);
  ledRed.Off();
  pinMode(BUILTIN_LED, OUTPUT);
  ledBuiltin.Blink(2000, 2000).Forever();

  // Let thermal sensor boot up
  delay(100); 
}

void loop() {

  // Wifi
  if (WiFi.status() != WL_CONNECTED) {
    ledBuiltin.Stop();
    wifiConnect();
    ledBuiltin.Blink(2000, 2000).Forever();
  }

  // OTA
  ArduinoOTA.handle();

  // HTTP server
  server.handleClient();

  // Remote debug
  Debug.handle();

  // Update leds
  ledRed.Update();
  ledBuiltin.Update();
}
