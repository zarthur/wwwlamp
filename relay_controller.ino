// Maurice Ribble
// 4-6-2008
// http://www.glacialwanderer.com/hobbyrobotics

// This code just lets you turn a digital out pin on and off.  That's
// all that is needed to verify a relay curcuit is working.
// Press the space bar to toggle the relay on and off.

// Arthur: Updated 29 July 2012 to support two pins/relays.

#define RELAY_PIN_0 3
#define RELAY_PIN_1 5

void setup()
{
  pinMode(RELAY_PIN_0, OUTPUT);
  pinMode(RELAY_PIN_1, OUTPUT);
  Serial.begin(9600); // open serial
  Serial.println("Press the spacebar to toggle relay on/off");
}

void loop()
{
  static int relayVal_0 = 0, relayVal_1 = 0;
  int cmd;

  while (Serial.available() > 0)
  {
    cmd = Serial.read();

    switch (cmd)
    {
    case '0':
      {
        relayVal_0 ^= 1; // xor current value with 1 (causes value to toggle)
        if (relayVal_0)
          Serial.println("Relay on");
        else
          Serial.println("Relay off");
        break;
      }
    case '1':
      {
        relayVal_1 ^= 1; // xor current value with 1 (causes value to toggle)
        if (relayVal_1)
          Serial.println("Relay on");
        else
          Serial.println("Relay off");
        break;
      }
    default:
      {
        Serial.println("Press the spacebar to toggle relay on/off");
      }
    }

    if (relayVal_0)
      digitalWrite(RELAY_PIN_0, HIGH);
    else
      digitalWrite(RELAY_PIN_0, LOW);

    if (relayVal_1)
      digitalWrite(RELAY_PIN_1, HIGH);
    else
      digitalWrite(RELAY_PIN_1, LOW);
    }
}
