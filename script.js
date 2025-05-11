// JavaScript to handle user interactions and backend communication

// Replace the textarea with a CodeMirror instance
const codeMirrorEditor = CodeMirror.fromTextArea(document.getElementById('codeInput'), {
    mode: 'python',
    lineNumbers: true,
    theme: 'default',
    indentUnit: 4,
    tabSize: 4,
    lineWrapping: true
});

// Adjust the scaleFlowchart function to ensure the SVG fits perfectly
function scaleFlowchart() {
    const flowchartContainer = document.getElementById('flowchart');
    const svgElement = flowchartContainer.querySelector('svg');

    if (svgElement) {
        const containerWidth = flowchartContainer.offsetWidth;
        const containerHeight = flowchartContainer.offsetHeight;
        const viewBox = svgElement.viewBox.baseVal;

        if (viewBox && viewBox.width > 0 && viewBox.height > 0) {
            const scaleX = containerWidth / viewBox.width;
            const scaleY = containerHeight / viewBox.height;
            const scale = Math.min(scaleX, scaleY); // Use the smaller scale to fit both dimensions

            svgElement.style.width = `${viewBox.width * scale}px`;
            svgElement.style.height = `${viewBox.height * scale}px`;
            svgElement.style.transform = 'translate(-50%, -50%)'; // Center the SVG
            svgElement.style.position = 'absolute';
            svgElement.style.left = '50%';
            svgElement.style.top = '50%';
        }
    }
}

// Call scaleFlowchart after the flowchart is rendered
function renderFlowchart(flowchartSVG) {
    const flowchartContainer = document.getElementById('flowchart');
    flowchartContainer.innerHTML = flowchartSVG;

    const svgElement = flowchartContainer.querySelector('svg');
    if (svgElement) {
        svgElement.style.width = '100%';
        svgElement.style.height = 'auto';
        applySuccessPathStyling(svgElement); // Apply success path styling
    }
}

document.getElementById('generateButton').addEventListener('click', async () => {
    const codeInput = codeMirrorEditor.getValue(); // Fetch code from CodeMirror editor
    const flowchartContainer = document.getElementById('flowchart');

    // Clear previous flowchart and show loading message
    flowchartContainer.innerHTML = '<p>Generating flowchart...</p>';

    if (!codeInput.trim()) {
        flowchartContainer.innerHTML = '<p class="error">Error: No Python code provided.</p>';
        return;
    }

    try {
        // Send POST request to backend with Python code
        const response = await fetch('http://127.0.0.1:5000/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain'
            },
            body: codeInput
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
        }

        // Get the SVG flowchart from the response
        const flowchartSVG = await response.text();

        // Render the flowchart
        renderFlowchart(flowchartSVG);
    } catch (error) {
        console.error('Error generating flowchart:', error);
        flowchartContainer.innerHTML = '<p class="error">An error occurred while generating the flowchart. Please check your Python code and try again.</p>';
    }
});

document.addEventListener('DOMContentLoaded', () => {
    scaleFlowchart();
});

// Syntax highlighting using Prism.js
Prism.highlightAll();

// Dynamic flowchart generation using jsPlumb
jsPlumb.ready(function () {
    const instance = jsPlumb.getInstance({
        Connector: ["Bezier", { curviness: 50 }],
        PaintStyle: { stroke: "#4a90e2", strokeWidth: 2 },
        EndpointStyle: { fill: "#4a90e2", radius: 5 },
        HoverPaintStyle: { stroke: "#ff512f", strokeWidth: 3 },
        ConnectionOverlays: [
            ["Arrow", { width: 10, length: 10, location: 1 }]
        ]
    });

    // Example: Connect nodes dynamically
    instance.connect({
        source: "startNode",
        target: "processNode"
    });
    instance.connect({
        source: "processNode",
        target: "endNode"
    });
});

// Export flowchart as image or PDF
function exportFlowchart() {
    const svgElement = document.querySelector("#flowchart svg");
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const img = new Image();

    img.onload = function () {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        const link = document.createElement("a");
        link.download = "flowchart.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    };

    img.src = "data:image/svg+xml;base64," + btoa(svgString);
}

// Tooltip initialization
const tooltips = document.querySelectorAll(".tooltip");
tooltips.forEach(tooltip => {
    tooltip.addEventListener("mouseover", () => {
        const tooltipText = tooltip.querySelector(".tooltiptext");
        tooltipText.style.visibility = "visible";
        tooltipText.style.opacity = "1";
    });
    tooltip.addEventListener("mouseout", () => {
        const tooltipText = tooltip.querySelector(".tooltiptext");
        tooltipText.style.visibility = "hidden";
        tooltipText.style.opacity = "0";
    });
});

// Add a global error handler to log any JavaScript errors
window.addEventListener('error', (event) => {
    console.error('Global error caught:', event.message, 'at', event.filename, 'line', event.lineno);
});

// Ensure the DOM is fully loaded before attaching event listeners

// Removed the event listener and initialization for dark mode toggle

// Resizable split-view container
const divider = document.querySelector('.divider');
const editorPane = document.querySelector('.editor-pane');
const flowchartPane = document.querySelector('.flowchart-pane');

let isResizing = false;

divider.addEventListener('mousedown', () => {
    isResizing = true;
    document.body.style.cursor = 'col-resize';
});

document.addEventListener('mousemove', (e) => {
    if (!isResizing) return;
    const totalWidth = editorPane.parentElement.offsetWidth;
    const editorWidth = e.clientX;
    editorPane.style.flex = `${editorWidth / totalWidth}`;
    flowchartPane.style.flex = `${1 - editorWidth / totalWidth}`;
});

document.addEventListener('mouseup', () => {
    isResizing = false;
    document.body.style.cursor = 'default';
});

// Highlight corresponding flowchart node on hover
const editor = CodeMirror.fromTextArea(document.getElementById('codeInput'), {
    mode: 'python',
    lineNumbers: true,
    theme: 'default',
});

editor.on('cursorActivity', () => {
    const line = editor.getCursor().line;
    const flowchartNode = document.querySelector(`[data-line="${line}"]`);
    if (flowchartNode) {
        flowchartNode.classList.add('highlight');
    }
});

// Removed event listeners and logic for export buttons and dark mode toggle
const exportSVGButton = null;
const exportMermaidButton = null;

// Generate Mermaid code for the flowchart
function generateMermaidCode() {
    const codeInput = codeMirrorEditor.getValue();
    // Placeholder logic to convert Python code to Mermaid syntax
    return `graph TD\n    A[Start] --> B[Process] --> C[End]`;
}

// Collapsible examples sidebar
const sidebar = document.querySelector('.examples-sidebar');
const toggleButton = document.querySelector('.examples-sidebar .toggle-button');

toggleButton.addEventListener('click', () => {
    sidebar.classList.toggle('open');
});

fetch('/example_program')
    .then((response) => response.json())
    .then((data) => {
        const examplesList = document.createElement('ul');
        data.example_code.split('\n\n').forEach((example, index) => {
            const listItem = document.createElement('li');
            listItem.textContent = `Example ${index + 1}`;
            listItem.addEventListener('click', () => {
                editor.setValue(example);
            });
            examplesList.appendChild(listItem);
        });
        sidebar.appendChild(examplesList);
    });

// Add loading spinner to the Generate button
const generateButton = document.getElementById('generateButton');

generateButton.addEventListener('click', () => {
    generateButton.classList.add('loading');
    generateButton.disabled = true;

    // Simulate backend call
    setTimeout(() => {
        generateButton.classList.remove('loading');
        generateButton.disabled = false;
    }, 2000); // Replace with actual backend call
});

// Apply success path styling
function applySuccessPathStyling(svgElement) {
    const successEdges = svgElement.querySelectorAll('path[edge-label="Success"]');
    successEdges.forEach(edge => {
        edge.classList.add('success');
    });
}

// Call the function after rendering the SVG
const svgElement = document.querySelector('svg');
if (svgElement) {
    applySuccessPathStyling(svgElement);
}