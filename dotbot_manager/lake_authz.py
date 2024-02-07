import lakers

W = bytes.fromhex("4E5E15AB35008C15B89E91F9F329164D4AACD53D9923672CE0019F9ACD98573F")
KID_I = 0x2b
CRED_V = bytes.fromhex("a2026b6578616d706c652e65647508a101a501020241322001215820bbc34960526ea4d32e940cad2a234148ddc21791a12afbcbac93622046dd44f02258204519e257236b2a0ce2023f0931f1f386ca7afda64fcde0108c224c51eabf6072")

class LakeAuthz:
    def __init__(self):
        self.enrollment_server = lakers.AuthzEnrollmentServer(
                W,
                CRED_V,
                [KID_I],
        )
