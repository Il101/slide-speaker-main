#!/usr/bin/env python3
"""
Test Google TTS with SSML to verify it works correctly
"""
import os
from google.cloud import texttospeech_v1beta1

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/iliazarikov/Documents/Python_crypto/Barahlo/slide-speaker-main/inspiring-keel-473421-j2-22cc51dfb336.json'

def test_ssml_basic():
    """Test basic SSML with mark tags"""
    print("🧪 Testing Google TTS with SSML mark tags...")
    
    client = texttospeech_v1beta1.TextToSpeechClient()
    
    # Simple SSML with mark tag
    ssml_text = '''<speak>
<mark name="start"/>Привет мир.
<mark name="middle"/>Это тест.
<mark name="end"/>Спасибо.
</speak>'''
    
    print(f"📝 SSML input:\n{ssml_text}\n")
    
    # Create synthesis input
    synthesis_input = texttospeech_v1beta1.SynthesisInput(ssml=ssml_text)
    
    # Voice configuration
    voice = texttospeech_v1beta1.VoiceSelectionParams(
        language_code='ru-RU',
        name='ru-RU-Wavenet-D'
    )
    
    # Audio configuration
    audio_config = texttospeech_v1beta1.AudioConfig(
        audio_encoding=texttospeech_v1beta1.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000
    )
    
    # Request with time pointing enabled
    request = texttospeech_v1beta1.SynthesizeSpeechRequest(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
        enable_time_pointing=[texttospeech_v1beta1.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
    )
    
    print("🔊 Synthesizing speech...")
    response = client.synthesize_speech(request=request)
    
    print(f"✅ Audio generated: {len(response.audio_content)} bytes")
    
    # Check timepoints
    if hasattr(response, 'timepoints') and response.timepoints:
        print(f"✅ Timepoints returned: {len(response.timepoints)}")
        for tp in response.timepoints:
            print(f"   - Mark '{tp.mark_name}' at {tp.time_seconds:.2f}s")
    else:
        print("❌ No timepoints returned!")
    
    # Save audio for manual testing
    output_file = '/tmp/test_google_tts_ssml.wav'
    with open(output_file, 'wb') as f:
        f.write(response.audio_content)
    print(f"💾 Audio saved to: {output_file}")
    print(f"🎧 Listen to verify that tags are NOT spoken")
    print(f"   Run: afplay {output_file}")


def test_ssml_with_prosody():
    """Test SSML with prosody and mark tags"""
    print("\n🧪 Testing SSML with prosody...")
    
    client = texttospeech_v1beta1.TextToSpeechClient()
    
    # SSML with prosody and marks
    ssml_text = '''<speak>
<prosody rate="95%">
<mark name="w1"/>Сегодня <mark name="w2"/>прекрасный <mark name="w3"/>день.
</prosody>
</speak>'''
    
    print(f"📝 SSML input:\n{ssml_text}\n")
    
    synthesis_input = texttospeech_v1beta1.SynthesisInput(ssml=ssml_text)
    
    voice = texttospeech_v1beta1.VoiceSelectionParams(
        language_code='ru-RU',
        name='ru-RU-Wavenet-D'
    )
    
    audio_config = texttospeech_v1beta1.AudioConfig(
        audio_encoding=texttospeech_v1beta1.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000
    )
    
    request = texttospeech_v1beta1.SynthesizeSpeechRequest(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
        enable_time_pointing=[texttospeech_v1beta1.SynthesizeSpeechRequest.TimepointType.SSML_MARK]
    )
    
    print("🔊 Synthesizing speech...")
    response = client.synthesize_speech(request=request)
    
    print(f"✅ Audio generated: {len(response.audio_content)} bytes")
    
    if hasattr(response, 'timepoints') and response.timepoints:
        print(f"✅ Timepoints returned: {len(response.timepoints)}")
        for tp in response.timepoints:
            print(f"   - Mark '{tp.mark_name}' at {tp.time_seconds:.2f}s")
    else:
        print("❌ No timepoints returned!")
    
    output_file = '/tmp/test_google_tts_prosody.wav'
    with open(output_file, 'wb') as f:
        f.write(response.audio_content)
    print(f"💾 Audio saved to: {output_file}")
    print(f"🎧 Listen to verify: afplay {output_file}")


if __name__ == '__main__':
    try:
        test_ssml_basic()
        test_ssml_with_prosody()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
