import Foundation
import ImageIO
import Vision

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write(Data("Usage: ocr_image.swift <image>\n".utf8))
    exit(2)
}

let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
guard let source = CGImageSourceCreateWithURL(imageURL as CFURL, nil),
      let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
    FileHandle.standardError.write(Data("Unable to open image\n".utf8))
    exit(3)
}

func recognise(level: VNRequestTextRecognitionLevel, languages: [String]?) throws -> [VNRecognizedTextObservation] {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = level
    request.usesLanguageCorrection = level == .accurate
    if let languages {
        request.recognitionLanguages = languages
    }
    try VNImageRequestHandler(cgImage: image, options: [:]).perform([request])
    return request.results ?? []
}

var observations: [VNRecognizedTextObservation] = []
var lastError: Error?
let attempts: [(VNRequestTextRecognitionLevel, [String]?)] = [
    (.accurate, ["en-US", "zh-Hans"]),
    (.accurate, ["en-US"]),
    (.accurate, nil),
    (.fast, ["en-US"]),
    (.fast, nil),
]

for (level, languages) in attempts {
    do {
        observations = try recognise(level: level, languages: languages)
        if !observations.isEmpty { break }
    } catch {
        lastError = error
    }
}

if observations.isEmpty, let lastError {
    FileHandle.standardError.write(Data("OCR failed after local fallback attempts: \(lastError)\n".utf8))
    exit(4)
}

let sortedObservations = observations.sorted {
        if abs($0.boundingBox.maxY - $1.boundingBox.maxY) > 0.02 {
            return $0.boundingBox.maxY > $1.boundingBox.maxY
        }
        return $0.boundingBox.minX < $1.boundingBox.minX
}
for observation in sortedObservations {
    if let text = observation.topCandidates(1).first?.string {
        print(text)
    }
}
