#include <hidboot.h>
#include <usbhub.h>
#include <Mouse.h>
#include <hiduniversal.h>
#include <Wire.h>
#include <SPI.h>

#define RPT_LEN  8
#define BUFFER_SIZE 10  // Buffer for serial input parsing

USB Usb;
USBHub Hub(&Usb);
HIDUniversal Hid(&Usb);

class HIDMouseEvents {
  public:
    void OnButtonDn(uint8_t but_id) {
        Mouse.press(but_id);
    }
    void OnButtonUp(uint8_t but_id) {
        Mouse.release(but_id);
    }
    void Move(int8_t xm, int8_t ym, int8_t scr) {
        Mouse.move(xm, ym, scr);
    }
};

class HIDMouseReportParser : public HIDReportParser {
    HIDMouseEvents *mouEvents;
    uint8_t oldButtons;
  public:
    HIDMouseReportParser(HIDMouseEvents *evt) : mouEvents(evt), oldButtons(0) {}
    
    void Parse(USBHID *hid, bool is_rpt_id, uint8_t len, uint8_t *buf) {
        uint8_t buttons = buf[0]; // For mouse clicks
        if (buttons != oldButtons) {
            for (uint8_t but_id = 1; but_id <= 4; but_id <<= 1) {
                if (buttons & but_id) {
                    if (!(oldButtons & but_id)) mouEvents->OnButtonDn(but_id);
                } else {
                    if (oldButtons & but_id) mouEvents->OnButtonUp(but_id);
                }
            }
            oldButtons = buttons;
        }
        int8_t xm = buf[1], ym = buf[2], scr = buf[3]; // For mouse movements and scroll wheel
        if (xm || ym || scr) mouEvents->Move(xm, ym, scr);
    }
};

HIDMouseEvents MouEvents;
HIDMouseReportParser Mou(&MouEvents);
HIDBoot<USB_HID_PROTOCOL_MOUSE> HidMouse(&Usb);

char received_code[BUFFER_SIZE];  // Fixed-size buffer for input
uint8_t index1 = 0;

void setup() {
    Mouse.begin();
    Serial.begin(9600);
    Serial.setTimeout(1);
    Usb.Init();
    if (!Hid.SetReportParser(0, &Mou)) {
    }
}

void loop() {
    Usb.Task();  // Handle USB events

    while (Serial.available()) {
        char c = Serial.read();
        if (c == '*') {
            received_code[index1] = '\0';  // Null-terminate the string
            
            char *comma_pos = strchr(received_code, ',');
            if (comma_pos) {
                *comma_pos = '\0';  // Split the string at the comma
                int x_v = atoi(received_code);
                int y_v = atoi(comma_pos + 1);
                Mouse.move(x_v, y_v, 0);
                Mouse.click();
            }
            index1 = 0;  // Reset index for next input
        } 
        else if (index1 < BUFFER_SIZE - 1) {  // Prevent buffer overflow
            received_code[index1++] = c;
        }
    }
}
