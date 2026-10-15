# Third-party notices

## REA: Reverse Engineer Anything

REB adapts design concepts from REA (https://github.com/morluto/rea):
- the Evidence record (provider, operation, confidence, limitations, locations)
- the residual-unknown registry with revisions and evidence-backed resolution
- the rule that missing coverage is unknown, not absence
- the reconstruction obligation ledger (owner, required cases, verifier authority)
- the tool-shape guidance (inspect / search / trace / compare / workflow / observe)

REB does not include REA source code. REA is distributed under the MIT License:

```
MIT License

Copyright (c) 2026 morluto

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Optional dependencies

Installed only with extras, under their own licenses: pydantic (MIT), PyYAML (MIT),
mcp (MIT), openpyxl (MIT), pypdf (BSD-3), pytesseract (Apache-2.0), Pillow (MIT-CMU),
faster-whisper (MIT), pm4py (AGPL-3.0, optional; not imported by default).
