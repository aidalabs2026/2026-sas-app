class CBSDError:
    def __init__(self, code, name, message, severity):
        self.code = code
        self.name = name
        self.message = message
        self.severity = severity

    #def __str__(self):
    #    return f"Error Code: {self.code}, Name : {self.name}, Message: '{self.message}', Severity: {self.severity}"

    def __repr__(self):
        return f"CBSDError(code={self.code}, message='{self.message}', severity='{self.severity}')"

    def code(self):
        return self.code

    def name(self):
        return self.name

    def message(self):
        return self.message


# 예시 에러 코드 목록
class CBSDErrorCodes:
    ERROR_CODES = {
        "SUCCESS":CBSDError(0, "SUCCESS", "CBSD request is approved by SAS", "Low"),
        "VERSION": CBSDError(100, "VERSION", "SAS protocol version used by CBSD is not supported by SAS", "Low"),
        "BLACKLISTED": CBSDError(101, "BLACKLISTED", """"CBSD is blacklisted. This responseCode is 
            returned if the CBSD is under a SAS or FCC 
            enforcement action and is barred from CBRS 
            operation. In general, the CBSD should not try 
            to re-register until actions external to this 
            specification are taken. 
            Note: Blacklisting behavior by the SAS and 
            CBSD is FFS.
            """, "Medium"),
        "MISSING_PARAM": CBSDError(102, "MISSING_PARAM", "Required parameters missing", "High"),
        "INVALID_VALUE": CBSDError(103, "INVALID_VALUE", "One or more parameters have invalid value", "Critical"),
        "CERT_ERROR": CBSDError(104, "CERT_ERROR", """There is an error in the certificate used to make 
            the request (e.g. the credential is of the wrong 
            role).
            Note: Most certificate errors, such as expired or 
            syntactically invalid certificates, will cause 
            errors at the TLS connection.
            """, "Critical"),
        "DEREGISTER": CBSDError(105, "DEREGISTER", """A CBSD receiving this responseCode is 
            automatically deregistered by the SAS. The 
            CBSD shall cease all transmissions, terminate 
            all Grants, and consider itself Unregistered. The 
            SAS may include this responseCode parameter 
            in any message.
            The responseMessage parameter may contain a 
            string describing the reason for deregistration.
            See NOTE 1 below.""", "Critical"),
        "REG_PENDING": CBSDError(200, "REG_PENDING", """Incomplete registration information. The 
            registration process is pending. One or more 
            REG-Conditional parameters have not yet been 
            supplied to the SAS. The CBSD is likely to 
            accomplish a successful registration when the 
            missing registration information is made 
            available to the SAS.""", "Critical"),
        "GROUP_ERROR": CBSDError(201, "GROUP_ERROR", """An error has been identified in the grouping 
            parameters of the CBSD.""", "Critical"),
        "UNSUPPORTED_SPECTRUM": CBSDError(300, "UNSUPPORTED_SPECTRUM", """The frequency range indicated in the spectrum 
            inquiry request or grant request is at least 
            partially outside of the CBRS band.""", "Critical"),
        "INTERFERENCE": CBSDError(400, "INTERFERENCE", """Requested operation parameters cause too much 
            interference. This responseCode value indicates 
            that the Grant request is unlikely to be 
            successful if retried by the CBSD.""", "Critical"),
        "GRANT_CONFLICT": CBSDError(401, "GRANT_CONFLICT", """Conflict with an existing Grant of the same 
            CBSD. The CBSD should be able to remediate 
            this using the data returned in the responseData
            structure, by synchronizing its Grant state with 
            the SAS and relinquishing any out-of-sync 
            Grants.
            """, "Critical"),
        "TERMINATED_GRANT": CBSDError(500, "TERMINATED_GRANT", """The Grant is terminated. This condition occurs 
            if, for example, incumbent status has changed 
            permanently causing the current Grant to 
            terminate. The CBSD shall terminate radio 
            operation by turning off its radio transmission 
            associated with this Grant within 60 seconds 
            after the value of the transmitExpireTime
            parameter expires, in accordance with part 
            96.39(c)(2) (ref. [n.8]). The Grant is considered 
            terminated by the SAS, but the CBSD may 
            relinquish the Grant. If the operationParam
            parameter is included in the HeartbeatResponse
            object, the CBSD should consider it as a 
            recommendation by the SAS to obtain a new 
            Grant using the included operational parameter 
            values, and may request a new Grant using 
            those operational parameters.""", "Critical"),
        "SUSPENDED_GRANT": CBSDError(501, "SUSPENDED_GRANT", """The Grant is suspended. This condition occurs if 
            incumbent status has changed temporarily. The 
            CBSD shall terminate radio operation by 
            turning off its radio transmission associated 
            with this Grant within 60 seconds after the value 
            of the transmitExpireTime parameter expires, in 
            accordance with part 96.39(c)(2) (ref. [n.8]). In 
            such a case the CBSD may continue to send 
            HeartbeatRequest objects and waiting until the 
            Grant is re-enabled, or may relinquish the Grant 
            and request another. If the operationParam
            parameter is included in the HeartbeatResponse
            object, the CBSD should consider it as a 
            recommendation by the SAS to obtain a new 
            Grant using the included operational parameter 
            values, and may request a new Grant using 
            those parameters.""", "Critical"),
        "UNSYNC_OP_PARAM": CBSDError(502, "UNSYNC_OP_PARAM", """The Grant state is out of sync between the 
            CBSD and the SAS. The CBSD shall turn off 
            the radio transmission associated with this Grant 
            within 60 seconds from receiving this 
            responseCode value, in accordance with Part 
            96.39(c)(2) (ref. [n.8]), and shall relinquish this 
            Grant.
            """, "Critical"),

    }

    @classmethod
    def get_error(cls, code):
        return cls.ERROR_CODES.get(code, CBSDError(code, "UNKNOWN_ERROR", "Unknown error code.", "Unknown"))

# 사용 예시
if __name__ == "__main__":
    error = CBSDErrorCodes.get_error("SUCCESS")
    print(error.name)