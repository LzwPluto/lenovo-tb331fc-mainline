path = r"\\wsl.localhost\Ubuntu-24.04\home\pluto\kbuild\linux-next-tb128fu-hx83102-panel-port\.config"
with open(path, "r", encoding="utf-8") as f:
    cfg = f.read()

checks = [
    "CONFIG_SND_SOC_AW88166",
    "CONFIG_SND_SOC_SM8250",
    "CONFIG_SND_SOC_QCOM_COMMON",
    "CONFIG_SND_SOC_QCOM",
    "CONFIG_SND_SOC_QDSP6",
    "CONFIG_SND_SOC_QDSP6_AFE",
    "CONFIG_SND_SOC_QDSP6_ASM",
    "CONFIG_SND_SOC_QDSP6_ADM",
    "CONFIG_TYPEC_RT1711H",
    "CONFIG_TYPEC_TCPM",
    "CONFIG_TYPEC_TCPCI",
    "CONFIG_QCOM_FSA4480",
    "CONFIG_QRTR",
    "CONFIG_QRTR_SMD",
    "CONFIG_QCOM_Q6V5_PAS",
    "CONFIG_RPMSG_QCOM_GLINK_SMD"
]

for c in checks:
    matches = [l.strip() for l in cfg.splitlines() if c in l]
    print(f"{c}: {matches if matches else 'NOT FOUND'}")
