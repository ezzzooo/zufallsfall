import AppKit
import WebKit

// Aufruf: swift html2pdf.swift <eingabe.html> <ausgabe.pdf>
let args = CommandLine.arguments
let input = URL(fileURLWithPath: args[1])
let output = URL(fileURLWithPath: args[2])

class Delegate: NSObject, WKNavigationDelegate {
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            let info = NSPrintInfo()
            info.paperSize = NSSize(width: 595.28, height: 841.89) // A4
            info.topMargin = 50; info.bottomMargin = 56; info.leftMargin = 48; info.rightMargin = 48
            info.horizontalPagination = .fit
            info.verticalPagination = .automatic
            info.isHorizontallyCentered = false
            info.isVerticallyCentered = false
            info.jobDisposition = .save
            info.dictionary()[NSPrintInfo.AttributeKey.jobSavingURL] = output
            let op = webView.printOperation(with: info)
            op.showsPrintPanel = false
            op.showsProgressPanel = false
            op.view?.frame = webView.bounds
            op.runModal(for: NSWindow(), delegate: nil, didRun: nil, contextInfo: nil)
            DispatchQueue.main.asyncAfter(deadline: .now() + 2) { NSApp.terminate(nil) }
        }
    }
}

let app = NSApplication.shared
let web = WKWebView(frame: NSRect(x: 0, y: 0, width: 800, height: 1200))
let delegate = Delegate()
web.navigationDelegate = delegate
web.loadFileURL(input, allowingReadAccessTo: input.deletingLastPathComponent())
app.run()
