# patient_data.py  (same as yesterday – shown for clarity)
from dataclasses import dataclass, asdict
import yaml, re, dateparser

DIGIT = re.compile(r'\d')

@dataclass
class PatientData:
    name: str|None = None
    phone: str|None = None
    phone_valid: bool = False
    phone_buffer: str = ""
    wa_opt_in: bool = False

    chief_concern: str|None = None
    iso_start: str|None = None
    duration_min: int|None = None
    calendar_link: str|None = None
    booked: bool = False

    # ── helpers ──────────────────────────────────────────
    def push_digits(self, txt:str):
        self.phone_buffer += "".join(DIGIT.findall(txt))
        if len(self.phone_buffer) >= 10:
            if not self.phone_buffer.startswith("92"):
                self.phone_buffer = "92" + self.phone_buffer[-10:]
            self.phone = "+" + self.phone_buffer
            self.phone_valid = True

    def maybe_parse_datetime(self, txt:str):
        if self.iso_start:               # already set
            return
        dt_obj = dateparser.parse(txt, settings={"PREFER_DATES_FROM":"future"})
        if dt_obj:
            self.iso_start = dt_obj.isoformat()

    def yaml_summary(self)->str:
        return yaml.dump(asdict(self), allow_unicode=True)
