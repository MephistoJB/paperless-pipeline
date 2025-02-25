/**
 * Adjusts the PDF image height based on the available window height.
 * This ensures that the PDF preview adapts dynamically to the viewport size.
 */
function updatePdfImageHeight() {
    const availableHeight = window.innerHeight - 80; // Calculate remaining height after subtracting navbar
    $('#pdfImage').css("maxHeight", availableHeight + 'px'); // Apply max height to the PDF image
    $('#height').text(`Navbar (${availableHeight}px)`); // Update the UI with the new height
}

/**
 * Fetches the rendered PDF image URL for a given document ID.
 * @param {number} docId - The ID of the document.
 * @returns {Promise<string|null>} - The URL of the rendered PDF image.
 */
async function renderPdf(docId) {
    try {
        // Request the image URL from the backend API
        const response = await $.getJSON(`/api/render_pdf/${docId}`);
        return response.image_url; // Return the received image URL
    } catch (error) {
        console.error("Error rendering PDF:", error);
        alert("Error rendering PDF."); // Notify the user about the failure
        return null; // Return null in case of an error
    }
}

/**
 * Loads the inbox list and initializes pagination.
 * The first document in the list is automatically loaded.
 */
function loadInboxList() {
    $.getJSON('/api/inbox_list')
        .done(function (inboxDict) {
            $("#pagination").empty(); // Clear existing pagination links

            let inboxArray = Object.entries(inboxDict); // Convert object to an array for easier processing
            if (inboxArray.length > 0) {
                loadDocument(inboxArray[0][0]); // Automatically load the first document in the inbox
            } else{
                loadDocument(-1); //If no Inbox Document is there, present the screen
            }  

            // Generate pagination links for each document in the inbox
            inboxArray.forEach((doc, index) => {
                let [docId, docName] = doc; // Extract document ID and name

                let pageItem = $('<li class="page-item"></li>'); // Create pagination list item
                let pageLink = $('<a class="page-link" href="#">' + (index + 1) + '</a>'); // Create clickable link

                // Add click event to load the corresponding document
                pageLink.click(function (event) {
                    event.preventDefault(); // Prevent default anchor behavior
                    loadDocument(docId); // Load the selected document
                });

                pageItem.append(pageLink); // Append link to pagination item
                $("#pagination").append(pageItem); // Add to pagination UI
            });
        })
        .fail(function () {
            console.error("Error loading inbox list."); // Log failure in console
        });
}

/**
 * Tags a document with a specific tag name.
 * @param {number} docId - The ID of the document.
 * @param {string} tagName - The name of the tag to be assigned.
 */
async function tagDocument(docId, tagName) {
    try {
        console.log(`Tagging document ${docId} with tag '${tagName}'...`);

        // Send a POST request to assign a tag to the document
        const response = await $.ajax({
            url: '/api/tag_document', // API endpoint for tagging
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ doc_id: docId, tag_name: tagName }) // Send document ID and tag name
        });

        console.log("Document tagged successfully:", response); // Log success response
        loadInboxList() // Reload
    } catch (error) {
        console.error("Error tagging document:", error); // Log error
    }
}

/**
 * Loads both document information and the corresponding PDF preview.
 * @param {number} docId - The ID of the document to load.
 */
async function loadDocument(docId) {
    try {
        // If no documents are available
        if (docId === -1) {
            $('#title').text(""); // Clear title
            $('#cor').text(""); // Clear sender
            $('#type').text(""); // Clear document type
            $('#path').text(""); // Clear storage path
            $('#tags').empty(); // Clear tags

            // Clear PDF display and show placeholder with red X
            const pdfContainer = $('#pdf-container');
            pdfContainer.empty().html(`
                <div class="d-flex justify-content-center align-items-center" style="height: 400px;">
                    <div class="text-center">
                        <span class="text-danger" style="font-size: 100px;">&#10060;</span>
                        <p class="text-danger fw-bold mt-2" style="font-size: 18px;">No Documents to process</p>
                    </div>
                </div>
            `);

            return; // Stop function execution, as there is no document to load
        }

        // Load regular document data
        const infoResponse = await $.getJSON(`/api/document_info/${docId}`);

        // Update document details in the UI
        $('#title').text(infoResponse.title);
        $('#cor').text(infoResponse.correspondent);
        $('#type').text(infoResponse.type);
        $('#path').text(infoResponse.storage_path);

        // Display tags as Bootstrap pill badges
        const tagsContainer = $('#tags');
        tagsContainer.empty();
        infoResponse.tags.forEach(tag => {
            const badge = $('<span></span>')
                .addClass('badge rounded-pill bg-danger me-1')
                .text(tag);
            tagsContainer.append(badge);
        });

        // Attach event listeners to buttons
        $('#btnNext').off('click').on('click', () => tagDocument(docId, "-Inbox"));
        $('#btnSendToAI').off('click').on('click', () => tagDocument(docId, "ai-title"));
        $('#btnInvestigate').off('click').on('click', () => tagDocument(docId, "check"));

        // Load and display the PDF preview
        const pdfImage = $('#pdfImage');
        const placeholder = $('#pdf-placeholder');

        pdfImage.hide();
        placeholder.addClass('d-flex').show();

        if (infoResponse.thumbnail_url) {
            pdfImage.attr('src', infoResponse.thumbnail_url).off('load error').on({
                'load': function () {
                    placeholder.removeClass('d-flex').hide();
                    pdfImage.show();
                    updatePdfImageHeight();
                },
                'error': function () {
                    placeholder.html('<p class="text-danger">Failed to load image.</p>');
                }
            });
        } else {
            placeholder.html('<p class="text-danger">Thumbnail not available.</p>');
        }

    } catch (error) {
        console.error("Error loading document:", error);
        alert("Error loading document.");
    }
}

/**
 * Initializes event listeners on page load.
 * - Handles sidebar toggle
 * - Binds the refresh metadata button
 * - Adjusts the PDF viewer height on window resize
 */
document.addEventListener('DOMContentLoaded', function () {
    $(window).on('resize', updatePdfImageHeight); // Adjust PDF viewer height dynamically
    loadInboxList(); // Load document list when page loads

    // Sidebar toggle functionality
    const sidebar = document.getElementById("sidebar");
    const content = document.getElementById("content");
    const toggleButton = document.getElementById("sidebarToggle");

    toggleButton.addEventListener("click", function () {
        sidebar.classList.toggle("collapsed"); // Toggle collapsed class on sidebar
        content.classList.toggle("collapsed"); // Adjust content area accordingly
    });

    // Refresh metadata button functionality
    $("#navRefresh").click(async function (event) {
        event.preventDefault(); // Prevent default behavior of the button
        try {
            const response = await fetch("/refreshMetadata"); // Send request to refresh metadata
            if (!response.ok) throw new Error(`Failed to refresh Metadata: ${response.statusText}`);
            console.log("Metadata successfully refreshed!"); // Log success message
        } catch (error) {
            console.error("Error refreshing metadata:", error); // Log error
        }
    });
});