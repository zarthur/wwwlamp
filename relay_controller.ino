#define RELAY_PIN_0 3
#define RELAY_PIN_1 5

void setup(){
  pinMode(RELAY_PIN_0, OUTPUT);
  pinMode(RELAY_PIN_1, OUTPUT);
  Serial.begin(9600);
}

void loop(){
  int cmd;
  while (Serial.available() > 0){
        cmd = Serial.read();

        switch (cmd){
            case '0':{
                digitalWrite(RELAY_PIN_0, LOW);
                break;
            }
            case '1':{
                digitalWrite(RELAY_PIN_0, HIGH);
                break;
            }
            case 'c':{
                digitalWrite(RELAY_PIN_1, LOW);
                break;
            }
            case 'o':{
                digitalWrite(RELAY_PIN_1, HIGH);
                break;
            }
        }
    }
}
