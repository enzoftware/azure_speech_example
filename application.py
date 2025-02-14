import requests
import base64
import json
import time
import random
import azure.cognitiveservices.speech as speechsdk

from flask import Flask, jsonify, render_template, request, make_response

app = Flask(__name__)

subscription_key = 'fe06d211d2424640a6f4ca56c204ef8b'
region = "centralus"
language = "en-US"
voice = "Microsoft Server Speech Text to Speech Voice (en-US, JennyNeural)"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/readalong")
def readalong():
    return render_template("readalong.html")

@app.route("/gettoken", methods=["POST"])
def gettoken():
    fetch_token_url = 'https://%s.api.cognitive.microsoft.com/sts/v1.0/issueToken' %region
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key
    }
    response = requests.post(fetch_token_url, headers=headers)
    access_token = response.text
    return jsonify({"at":access_token})


@app.route("/gettonguetwister", methods=["POST"])
def gettonguetwister():
    language = request.form.get("language")
    print(language)
    tonguetwisters = {
        "en-US": [
            "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
            "She sells seashells by the seashore.",
            "We surely shall see the sun shine soon.",
            "I scream, you scream, we all scream for ice cream.",
            "Red lorry, yellow lorry.",
            "Thin sticks, thick bricks.",
            "Susie works in a shoeshine shop. Where she shines she sits, and where she sits she shines."
        ],
        "es-ES": [
            "Tres tristes tigres tragan trigo en un trigal.",
            "El perro de San Roque no tiene rabo porque Ramón Ramírez se lo ha cortado.",
            "Pablito clavó un clavito en la calva de un calvito.",
            "Pepe pecas pica papas con un pico y una pala.",
            "El cielo está enladrillado, quién lo desenladrillará?",
            "Mi mamá me mima mucho."
        ],
        "ko-KR": [
            "간장 공장 공장장은 강 공장장이고 된장 공장 공장장은 장 공장장이다.",
            "고양이야 미안해 미안해 고양이야.",
            "철수 철쭉 철쭉 철수.",
            "오리 오리 오리.",
            "잘 자라, 잘 자라, 잘 자라.",
            "저기 저 사자가 사자 같다.",
            "감자 깎아 감자."
        ],
        "ja-JP": [
            "生麦生米生卵",
            "赤巻紙青巻紙黄巻紙",
            "東京特許許可局",
            "バスガス爆発",
            "隣の客はよく柿食う客だ",
            "坊主が屏風に上手に坊主の絵を描いた",
            "この竹垣に竹立てかけたのは、竹立てかけたかったから竹立てかけた"
        ],
        "zh-CN": [
            "四是四，十是十，十四是十四，四十是四十。",
            "吃葡萄不吐葡萄皮，不吃葡萄倒吐葡萄皮。",
            "天上天，下雨不愁；地下水，涨得满流。",
            "黑化肥发灰，灰化肥发黑。",
            "吃饭不忘种田，种田不忘吃饭。",
            "板凳长，板凳宽，板凳上面坐个胖胖胖胖。",
            "山前有个严岩，严岩背后有眼盐。"
        ]
    }

    if language not in tonguetwisters:
        return jsonify({"error": "Language not supported"}), 400

    return jsonify({"tt": random.choice(tonguetwisters[language])})

@app.route("/getstory", methods=["POST"])
def getstory():
    id = int(request.form.get("id"))
    stories = [["Read aloud the sentences on the screen.",
        "We will follow along your speech and help you learn speak English.",
        "Good luck for your reading lesson!"],
        ["The Hare and the Tortoise",
        "Once upon a time, a Hare was making fun of the Tortoise for being so slow.",
        "\"Do you ever get anywhere?\" he asked with a mocking laugh.",
        "\"Yes,\" replied the Tortoise, \"and I get there sooner than you think. Let us run a race.\"",
        "The Hare was amused at the idea of running a race with the Tortoise, but agreed anyway.",
        "So the Fox, who had consented to act as judge, marked the distance and started the runners off.",
        "The Hare was soon far out of sight, and in his overconfidence,",
        "he lay down beside the course to take a nap until the Tortoise should catch up.",
        "Meanwhile, the Tortoise kept going slowly but steadily, and, after some time, passed the place where the Hare was sleeping.",
        "The Hare slept on peacefully; and when at last he did wake up, the Tortoise was near the goal.",
        "The Hare now ran his swiftest, but he could not overtake the Tortoise in time.",
        "Slow and Steady wins the race."],
        ["The Ant and The Dove",
        "A Dove saw an Ant fall into a brook.",
        "The Ant struggled in vain to reach the bank,",
        "and in pity, the Dove dropped a blade of straw close beside it.",
        "Clinging to the straw like a shipwrecked sailor, the Ant floated safely to shore.",
        "Soon after, the Ant saw a man getting ready to kill the Dove with a stone.",
        "Just as he cast the stone, the Ant stung the man in the heel, and he missed his aim,",
        "The startled Dove flew to safety in a distant wood and lived to see another day.",
        "A kindness is never wasted."]]
    if(id >= len(stories)):
        return jsonify({"code":201})
    else:
        return jsonify({"code":200,"storyid":id , "storynumelements":len(stories[id]),"story": stories[id]})

@app.route("/ackaud", methods=["POST"])
def ackaud():
    f = request.files['audio_data']
    reftext = request.form.get("reftext")
    language = request.form.get("language")
    print(language)
    #    f.save(audio)
    #print('file uploaded successfully')

    # a generator which reads audio data chunk by chunk
    # the audio_source can be any audio input stream which provides read() method, e.g. audio file, microphone, memory stream, etc.
    def get_chunk(audio_source, chunk_size=1024):
        while True:
            #time.sleep(chunk_size / 32000) # to simulate human speaking rate
            chunk = audio_source.read(chunk_size)
            if not chunk:
                #global uploadFinishTime
                #uploadFinishTime = time.time()
                break
            yield chunk

    # build pronunciation assessment parameters
    referenceText = reftext
    pronAssessmentParamsJson = "{\"ReferenceText\":\"%s\",\"GradingSystem\":\"HundredMark\",\"Dimension\":\"Comprehensive\",\"EnableMiscue\":\"True\"}" % referenceText
    pronAssessmentParamsBase64 = base64.b64encode(bytes(pronAssessmentParamsJson, 'utf-8'))
    pronAssessmentParams = str(pronAssessmentParamsBase64, "utf-8")

    # build request
    url = "https://%s.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=%s&usePipelineVersion=0" % (region, language)
    headers = { 'Accept': 'application/json;text/xml',
                'Connection': 'Keep-Alive',
                'Content-Type': 'audio/wav; codecs=audio/pcm; samplerate=16000',
                'Ocp-Apim-Subscription-Key': subscription_key,
                'Pronunciation-Assessment': pronAssessmentParams,
                'Transfer-Encoding': 'chunked',
                'Expect': '100-continue' }

    #audioFile = open('audio.wav', 'rb')
    audioFile = f
    # send request with chunked data
    response = requests.post(url=url, data=get_chunk(audioFile), headers=headers)
    #getResponseTime = time.time()
    audioFile.close()

    #latency = getResponseTime - uploadFinishTime
    #print("Latency = %sms" % int(latency * 1000))

    print(response.json())

    return response.json()

@app.route("/gettts", methods=["POST"])
def gettts():
    reftext = request.form.get("reftext")
    language = request.form.get("language")

    # Mapping of languages to their respective voice names
    language_to_voice = {
        "en-US": "Microsoft Server Speech Text to Speech Voice (en-US, JennyNeural)",
        "es-ES": "Microsoft Server Speech Text to Speech Voice (es-ES, ElviraNeural)",
        "ja-JP": "Microsoft Server Speech Text to Speech Voice (ja-JP, NanamiNeural)",
        "ko-KR": "Microsoft Server Speech Text to Speech Voice (ko-KR, SunHiNeural)",
        "zh-CN": "Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)",
    }

    # Creates an instance of a speech config with specified subscription key and service region.
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_synthesis_voice_name = language_to_voice.get(language, language_to_voice[language])


    offsets=[]

    def wordbound(evt):
        offsets.append( evt.audio_offset / 10000)

    # Creates a speech synthesizer with a null output stream.
    # This means the audio output data will not be written to any output channel.
    # You can just get the audio from the result.
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

    # Subscribes to word boundary event
    # The unit of evt.audio_offset is tick (1 tick = 100 nanoseconds), divide it by 10,000 to convert to milliseconds.
    speech_synthesizer.synthesis_word_boundary.connect(wordbound)

    result = speech_synthesizer.speak_text_async(reftext).get()
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        #print("Speech synthesized for text [{}]".format(reftext))
        #print(offsets)
        audio_data = result.audio_data
        #print(audio_data)
        #print("{} bytes of audio data received.".format(len(audio_data)))

        response = make_response(audio_data)
        response.headers['Content-Type'] = 'audio/wav'
        response.headers['Content-Disposition'] = 'attachment; filename=sound.wav'
        # response.headers['reftext'] = reftext
        response.headers['offsets'] = offsets
        return response

    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
        return jsonify({"success":False})

@app.route("/getttsforword", methods=["POST"])
def getttsforword():
    word = request.form.get("word")

    # Creates an instance of a speech config with specified subscription key and service region.
    speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
    speech_config.speech_synthesis_voice_name = voice

    # Creates a speech synthesizer with a null output stream.
    # This means the audio output data will not be written to any output channel.
    # You can just get the audio from the result.
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

    result = speech_synthesizer.speak_text_async(word).get()
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        #print("Speech synthesized for text [{}]".format(reftext))
        #print(offsets)
        audio_data = result.audio_data
        #print(audio_data)
        #print("{} bytes of audio data received.".format(len(audio_data)))

        response = make_response(audio_data)
        response.headers['Content-Type'] = 'audio/wav'
        response.headers['Content-Disposition'] = 'attachment; filename=sound.wav'
        # response.headers['word'] = word
        return response

    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
        return jsonify({"success":False})
