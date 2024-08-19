from pydantic import BaseModel, Field


class ChordJson(BaseModel):
    chord: str = Field(None, description='Chord name defined from musicpy', example='Cmaj')
    intervals: list = Field(None, description='Rhythm of the chord', example=[1/8, 1/8, 1/8, 1/8])
    pattern: list = Field(None, description='Pattern of the chord', example=[1.0, 3.0, 4.0, 1.1, 4.0, 3.0])
    pitch: int = Field(4, description='Pitch of the chord', example=4)