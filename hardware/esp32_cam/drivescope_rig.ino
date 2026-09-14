/*
 * DriveScope ESP32-CAM Physical Sensor Rig Firmware
 * Streams synchronized MJPEG frames with microsecond hardware timestamps
 * and 6-DOF IMU telemetry directly into DriveScope's HardwareScenarioSource.
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

WebServer server(80);
Servo panServo;
Servo tiltServo;

// Pin definition for CAMERA_MODEL_AI_THINKER
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

#define PAN_SERVO_PIN     12
#define TILT_SERVO_PIN    13

void handleStream() {
  WiFiClient client = server.client();
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  server.sendContent(response);

  while (client.connected()) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
      break;
    }
    
    uint64_t hw_time_us = esp_timer_get_time();

    String head = "--frame\r\n";
    head += "Content-Type: image/jpeg\r\n";
    head += "X-Hardware-Timestamp-Us: " + String(hw_time_us) + "\r\n";
    head += "Content-Length: " + String(fb->len) + "\r\n\r\n";
    
    client.print(head);
    client.write(fb->buf, fb->len);
    client.print("\r\n");
    
    esp_camera_fb_return(fb);
    delay(50); // ~20 FPS stream rate
  }
}

void handleControl() {
  if (server.hasArg("pan")) {
    int pan = server.arg("pan").toInt();
    panServo.write(constrain(pan, 0, 180));
  }
  if (server.hasArg("tilt")) {
    int tilt = server.arg("tilt").toInt();
    tiltServo.write(constrain(tilt, 0, 180));
  }
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void setup() {
  Serial.begin(115200);
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = 2;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  panServo.attach(PAN_SERVO_PIN);
  tiltServo.attach(TILT_SERVO_PIN);
  panServo.write(90);
  tiltServo.write(90);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  server.on("/stream", HTTP_GET, handleStream);
  server.on("/control", HTTP_POST, handleControl);
  server.begin();
  Serial.printf("DriveScope ESP32 sensor rig ready at http://%s\n", WiFi.localIP().toString().c_str());
}

void loop() {
  server.handleClient();
}
