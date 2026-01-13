const int trig1 = 2, echo1 = 3; 
const int trig2 = 4, echo2 = 5; 
const int potPin = A0;
const int greenLed = 8;
const int redLed = 9;

void setup() {
  Serial.begin(9600);
  pinMode(trig1, OUTPUT); pinMode(echo1, INPUT);
  pinMode(trig2, OUTPUT); pinMode(echo2, INPUT);
  pinMode(greenLed, OUTPUT); pinMode(redLed, OUTPUT);
}

float getDistance(int trig, int echo) {
  digitalWrite(trig, LOW); delayMicroseconds(2);
  digitalWrite(trig, HIGH); delayMicroseconds(10);
  digitalWrite(trig, LOW);
  long duration = pulseIn(echo, HIGH, 30000);
  if (duration == 0) return -1;
  return duration * 0.034 / 2;
}

void loop() {
  float sea = getDistance(trig1, echo1);
  float lake = getDistance(trig2, echo2);
  if (sea < 0 || lake < 0) return; 

  float head_m = abs(lake - sea) / 100.0;
  int wasteIntensity = analogRead(potPin);

  // Python 전송용 데이터

  Serial.print(sea, 2);    // 해수위 (m 단위)
  Serial.print("|");
  Serial.print(lake, 2);   // 호수위 (m 단위)
  Serial.print("|");
  Serial.println(wasteIntensity);

  // 현장 LED 피드백
  if (wasteIntensity > 700) {
    digitalWrite(redLed, HIGH);
    digitalWrite(greenLed, LOW);
  } else {
    digitalWrite(redLed, LOW);
    digitalWrite(greenLed, HIGH);
  }
  delay(500);
}