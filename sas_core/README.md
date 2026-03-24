# SAS Core - Spectrum Access System Core Server

CBRS(Citizens Broadband Radio Service) 스펙트럼 접근 시스템의 핵심 서버.
CBSD 디바이스의 등록, 스펙트럼 조회, Grant 관리, Heartbeat 처리를 담당한다.

## 실행

```bash
cd sas_core
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
python main.py
# http://0.0.0.0:8000 에서 서비스
```

`config.json` 파일이 필요하다 (config.json.example 참조):
```json
{
    "host": "127.0.0.1",
    "user": "root",
    "password": "your_password",
    "database": "2024sas_dev",
    "sasurl": "http://127.0.0.1:8000/"
}
```

---

## CBSD API 로직 상세

### 1. REGISTER (`POST /regist`)

CBSD 디바이스를 SAS에 등록한다.

**요청:**
```json
{
    "userId": "mfsd-001",
    "fccId": "etri-00000001",
    "cbsdCategory": "B",
    "callSign": "n.a.",
    "cbsdSerialNumber": "322019410001013",
    "airInterface": { "radioTechnology": "5G", "supportedSpec": "LTE-Rel10" },
    "cbsdInfo": { "vendor": "ETRI" },
    "measCapability": "RECEIVED_POWER_WITHOUT_GRANT",
    "installationParam": {
        "latitude": 37.483993, "longitude": 128.012786,
        "height": 20.0, "heightType": "AGL",
        "indoorDeployment": false,
        "antennaAzimuth": 40.0, "antennaDowntilt": 0.0,
        "antennaGain": 22.5, "antennaBeamwidth": 65.0
    }
}
```

**처리 흐름:**
```
1. CBSD_ID 생성: "{userId}/{cbsdSerialNumber}"
   예: "mfsd-001/322019410001013"

2. 이미 등록된 CBSD인지 확인 (TD_CBSD_REGIST 테이블)
   ├─ 기존 등록: STATUS를 "REGIST"로 업데이트 → 성공 응답
   └─ 신규 등록: TD_CBSD_REGIST에 INSERT → 성공 응답

3. 저장되는 정보:
   - 기본: FCC_ID, CATEGORY, CALL_SIGN, USER_ID, SN
   - 무선: RADIO_TECH, SUPP_SPEC
   - 위치: LAT, LNG, HEIGHT, HEIGHT_TYPE, INDOOR
   - 안테나: ANT_AZIM, ANT_DWN, ANT_GAIN, ANT_BWIDTH
```

**응답:**
```json
{
    "cbsdId": "mfsd-001/322019410001013",
    "measReportConfig": ["EutraCarrierRssiAlways"],
    "response": { "responseCode": 0, "responseMessage": "SUCCESS" }
}
```

---

### 2. DEREGISTER (`POST /deregist`)

등록된 CBSD를 해제한다. 해당 CBSD의 모든 Grant도 함께 삭제된다.

**요청:**
```json
{ "cbsdId": "mfsd-001/322019410001013" }
```

**처리 흐름:**
```
1. 해당 CBSD의 모든 Grant 삭제 (TD_CBSD_GRANT에서 DELETE)
2. CBSD 상태를 "UNREGISTERED"로 변경 (TD_CBSD_REGIST)
3. 성공 응답 반환
```

**응답:**
```json
{
    "cbsdId": "mfsd-001/322019410001013",
    "response": { "responseCode": 0, "responseMessage": "SUCCESS" }
}
```

---

### 3. SPECTRUM INQUIRY (`POST /spectrumInquery`)

10개 채널(3300~3400 MHz, 10MHz 단위)의 사용 가능 여부를 조회한다.

**요청:**
```json
{
    "cbsdId": "mfsd-001/322019410001013",
    "inquiredSpectrum": [
        { "lowFrequency": 3300000000, "highFrequency": 3310000000 },
        { "lowFrequency": 3310000000, "highFrequency": 3320000000 },
        ...
        { "lowFrequency": 3390000000, "highFrequency": 3400000000 }
    ]
}
```

**처리 흐름 (spectrumInqueryBySD - Event SD 기반):**
```
1. CBSD_ID에서 MFSD_ID 추출
2. TD_CBSD_EVT_SD 테이블에서 해당 MFSD의 채널별 가용 전력 조회
   - SD_CH_1 ~ SD_CH_10 값 확인
3. 각 채널에 대해:
   ├─ SD_CH_n == 45 (dBm) → maxEirp: 30 (사용 가능)
   └─ SD_CH_n <= 0        → maxEirp: 0  (사용 불가)
4. 사용 불가 원인:
   - ESC 센서가 1차 사용자(incumbent) 감지
   - FSPA(위성보호구역) 간섭 제한
   - Application에 의한 주파수 예약
```

**채널-주파수 매핑:**
```
CH 1:  3300-3310 MHz
CH 2:  3310-3320 MHz
CH 3:  3320-3330 MHz
...
CH 10: 3390-3400 MHz
```

**응답:**
```json
{
    "cbsdId": "mfsd-001/322019410001013",
    "response": { "responseCode": 0, "responseMessage": "SUCCESS" },
    "availableChannel": [
        {
            "frequencyRange": { "lowFrequency": 3300000000, "highFrequency": 3310000000 },
            "channelType": "PAL",
            "ruleApplied": "FCC Part 96",
            "maxEirp": 30
        },
        {
            "frequencyRange": { "lowFrequency": 3310000000, "highFrequency": 3320000000 },
            "channelType": "PAL",
            "ruleApplied": "FCC Part 96",
            "maxEirp": 0
        },
        ...
    ]
}
```

---

### 4. GRANT (`POST /grant`)

특정 주파수 대역에 대한 송신 권한(Grant)을 요청한다.

**요청:**
```json
{
    "cbsdId": "mfsd-001/322019410001013",
    "operationParam": {
        "maxEirp": 30,
        "operationFrequencyRange": {
            "lowFrequency": 3330000000,
            "highFrequency": 3340000000
        }
    }
}
```

**처리 흐름:**
```
1. Grant ID 생성: "{cbsdId}/{lowFrequency_MHz}"
   예: "mfsd-001/322019410001013/3330.0"

2. 중복 Grant 확인
   └─ 이미 존재: GRANT_CONFLICT (401) 에러 반환

3. 채널 가용성 확인 (TD_CBSD_EVT_SD 조회)
   ├─ 채널 번호 계산: (lowFreq - 3300MHz) / 10MHz + 1
   ├─ SD_CH_n 값 확인
   ├─ 가용 전력 > 0: Grant 승인
   └─ 가용 전력 <= 0: UNSUPPORTED_SPECTRUM (300) 에러 반환

4. Grant 승인 시:
   - TD_CBSD_GRANT에 INSERT
   - 상태: GRANTED
   - 만료시간: 현재시간 + GRANT_EXPIRETIME(설정값, 기본 600초)
   - Heartbeat 간격: 60초

5. Grant 후 CBSD는 Heartbeat를 주기적으로 전송해야 Grant 유지
```

**응답 (성공):**
```json
{
    "cbsdId": "mfsd-001/322019410001013",
    "grantId": "mfsd-001/322019410001013/3330.0",
    "transmitExpireTime": "2026-03-24T12:00:00Z",
    "grantExpireTime": "2026-03-24T12:00:00Z",
    "heartbeatDuration": 60,
    "heartbeatInterval": 60,
    "operationParam": {
        "maxEirp": 30,
        "operationFrequencyRange": { "lowFrequency": 3330000000, "highFrequency": 3340000000 }
    },
    "channelType": "PAL",
    "response": { "responseCode": 0, "responseMessage": "SUCCESS" }
}
```

**에러 응답:**
| responseCode | 이름 | 원인 |
|-------------|------|------|
| 401 | GRANT_CONFLICT | 동일 주파수에 이미 Grant 존재 |
| 300 | UNSUPPORTED_SPECTRUM | 요청 주파수 사용 불가 |

---

### 5. HEARTBEAT (`POST /heartbeat`)

Grant를 유지하기 위한 주기적 상태 보고. CBSD는 Grant 획득 후 heartbeatInterval 간격으로 전송해야 한다.

**요청:**
```json
{
    "cbsdId": "mfsd-001/322019410001013",
    "grantId": "mfsd-001/322019410001013/3330.0",
    "grantRenew": false,
    "operationState": "AUTHORIZED",
    "measReport": {}
}
```

**처리 흐름:**
```
1. 시스템 설정 로드
   - HEARTBEAT_INTERVAL: Heartbeat 주기 (기본 60초)
   - GRANT_EXPIRETIME: Grant 만료 시간 (기본 600초)
   - OPERPARAM_ON: 강제 채널 이동 설정 (0=Off)

2. Grant 유효성 확인 (TD_CBSD_GRANT 조회)
   └─ Grant 없음: TERMINATED_GRANT (500) 반환

3. Grant 상태 분기:

   ┌─ SUSPEND_AT = 1 (정지 상태)
   │  → SUSPENDED_GRANT (501) 반환
   │  → transmitExpireTime = 현재시간 (즉시 송신 중지)
   │
   ├─ EVENT_TRIGGER = "TERMINATED_GRANT" (시뮬레이션)
   │  → TERMINATED_GRANT (500) 반환
   │
   ├─ EVENT_TRIGGER = "UNSYNC_OP_PARAM" (시뮬레이션)
   │  → UNSYNC_OP_PARAM (502) 반환
   │
   └─ 정상 상태
      ├─ STATUS가 GRANTED → AUTHORIZED로 변경 (WebSocket 브로드캐스트)
      ├─ grantRenew = true → grantExpireTime 갱신 (+ GRANT_EXPIRETIME 초)
      └─ grantRenew = false → transmitExpireTime만 갱신

4. OPERPARAM_ON ≠ 0인 경우:
   → 응답에 operationParam 포함 (강제 채널 이동 지시)
```

**Grant 상태 전이:**
```
GRANTED ──(첫 Heartbeat 성공)──→ AUTHORIZED
AUTHORIZED ──(ESC 감지)──→ SUSPENDED (suspend_at=1)
SUSPENDED ──(ESC 해제)──→ AUTHORIZED (suspend_at=0)
AUTHORIZED ──(만료/종료)──→ TERMINATED
```

**응답 (정상):**
```json
{
    "cbsdId": "mfsd-001/322019410001013",
    "grantId": "mfsd-001/322019410001013/3330.0",
    "grantRenew": false,
    "operationStatusReq": true,
    "transmitExpireTime": "2026-03-24T12:10:00Z",
    "grantExpireTime": "",
    "heartbeatDuration": 10,
    "heartbeatInterval": 10,
    "response": { "responseCode": 0, "responseMessage": "SUCCESS" }
}
```

**Heartbeat 응답 코드:**
| responseCode | 이름 | 의미 | CBSD 동작 |
|-------------|------|------|----------|
| 0 | SUCCESS | 정상 | 송신 계속, 다음 HB 대기 |
| 500 | TERMINATED_GRANT | Grant 종료 | 60초 내 송신 중지, Grant 포기 |
| 501 | SUSPENDED_GRANT | Grant 일시정지 | 60초 내 송신 중지, HB 계속 전송하며 대기 |
| 502 | UNSYNC_OP_PARAM | 파라미터 불일치 | 송신 중지, Grant Relinquish |

---

### 6. RELINQUISHMENT (`POST /relinquishment`)

CBSD가 자발적으로 Grant를 반납한다.

**요청:**
```json
{
    "cbsdId": "mfsd-001/322019410001013",
    "grantId": "mfsd-001/322019410001013/3330.0"
}
```

**처리 흐름:**
```
1. Grant 존재 확인 (TD_CBSD_GRANT)
2. Grant 삭제 (Hard DELETE)
3. 성공 응답 반환
```

**응답:**
```json
{
    "cbsdId": "mfsd-001/322019410001013",
    "grantId": "mfsd-001/322019410001013/3330.0",
    "response": { "responseCode": 0, "responseMessage": "SUCCESS" }
}
```

---

## CBSD 전체 워크플로우

```
                    CBSD Emulator                          SAS Core
                         │                                     │
                         │──── POST /regist ──────────────────→│
                         │     (디바이스 정보)                    │ → TD_CBSD_REGIST INSERT
                         │←─── cbsdId, SUCCESS ────────────────│
                         │                                     │
                         │──── POST /spectrumInquery ─────────→│
                         │     (10개 채널 조회)                  │ → TD_CBSD_EVT_SD 조회
                         │←─── availableChannel[] ─────────────│
                         │                                     │
                         │──── POST /grant ───────────────────→│
                         │     (주파수 범위)                     │ → 가용성 확인
                         │←─── grantId, heartbeatInterval ─────│ → TD_CBSD_GRANT INSERT
                         │                                     │
                    ┌────┤                                     │
                    │    │──── POST /heartbeat ────────────────→│
                    │    │     (grantId, operationState)        │ → GRANTED→AUTHORIZED
                    │ 매 │←─── transmitExpireTime ─────────────│ → 만료시간 갱신
                    │ N초│                                     │
                    │    │──── POST /heartbeat ────────────────→│
                    │    │     (grantRenew: true)               │ → grantExpireTime 갱신
                    │    │←─── grantExpireTime ────────────────│
                    └────┤                                     │
                         │                                     │ ← ESC가 incumbent 감지
                         │──── POST /heartbeat ────────────────→│
                         │←─── SUSPENDED_GRANT (501) ──────────│ → suspend_at=1
                         │     (송신 중지, HB 계속)              │
                         │                                     │
                         │──── POST /relinquishment ──────────→│
                         │     (Grant 반납)                     │ → TD_CBSD_GRANT DELETE
                         │←─── SUCCESS ────────────────────────│
                         │                                     │
                         │──── POST /deregist ────────────────→│
                         │←─── SUCCESS ────────────────────────│ → Grant 전체 삭제
                         │                                     │   CBSD UNREGISTERED
```

---

## 에러 코드 일람

| Code | 이름 | 설명 |
|------|------|------|
| 0 | SUCCESS | 요청 승인 |
| 100 | VERSION | 프로토콜 버전 불일치 |
| 101 | BLACKLISTED | CBSD 블랙리스트 |
| 102 | MISSING_PARAM | 필수 파라미터 누락 |
| 103 | INVALID_VALUE | 잘못된 파라미터 값 |
| 104 | CERT_ERROR | 인증서 오류 |
| 105 | DEREGISTER | SAS에 의한 강제 해제 |
| 200 | REG_PENDING | 등록 보류 (추가 정보 필요) |
| 201 | GROUP_ERROR | 그룹 파라미터 오류 |
| 300 | UNSUPPORTED_SPECTRUM | 요청 주파수 사용 불가 |
| 400 | INTERFERENCE | 간섭 초과 |
| 401 | GRANT_CONFLICT | 기존 Grant와 충돌 |
| 500 | TERMINATED_GRANT | Grant 종료 (영구) |
| 501 | SUSPENDED_GRANT | Grant 일시정지 (임시) |
| 502 | UNSYNC_OP_PARAM | 운영 파라미터 불일치 |

---

## 시스템 설정 (TD_SYSTEM_PROP)

| Key | 기본값 | 설명 |
|-----|--------|------|
| HEARTBEAT_INTERVAL | 60 | Heartbeat 주기 (초) |
| GRANT_EXPIRETIME | 600 | Grant 만료 시간 (초) |
| OPERPARAM_ON | 0 | 강제 채널 이동 (0=Off, 1~10=채널번호) |

---

## DB 테이블

| 테이블 | 용도 |
|--------|------|
| TD_CBSD_REGIST | CBSD 등록 정보 |
| TD_CBSD_GRANT | Grant (주파수 사용 권한) |
| TD_CBSD_EVT_SD | 채널별 가용 전력 (SF/SE/SN 병합 결과) |
| TD_ESC_REGIST | ESC 센서 등록 |
| TD_ESC_CHANNELS | ESC 채널 모니터링 상태 |
| TD_E_DPA | 보호구역 (Geometry) |
| TD_SYSTEM_MSG_LOG | API 메시지 로그 |
| TD_SYSTEM_PROP | 시스템 설정 Key-Value |
