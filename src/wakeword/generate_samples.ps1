Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$targetFile = $args[0]
$phrase = $args[1]
$rate = [int]$args[2]

$synth.Rate = $rate
$synth.SetOutputToWaveFile($targetFile)
$synth.Speak($phrase)
$synth.Dispose()
