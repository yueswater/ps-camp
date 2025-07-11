import re

def downgrade_headings(text: str) -> str:
    # 把 # 變成 ###，## 變成 ####
    text = re.sub(r"^#### (.*)", r"##### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^### (.*)", r"#### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^## (.*)", r"### \1", text, flags=re.MULTILINE)
    text = re.sub(r"^# (.*)", r"## \1", text, flags=re.MULTILINE)
    return text