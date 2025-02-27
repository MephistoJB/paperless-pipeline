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
        showToast("error", "Error rendering PDF");
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
            showToast("error", "Error loading inbox list.");
        });
}

/**
 * Displays a Bootstrap toast notification.
 * @param {string} type - The type of toast ("success" or "error").
 * @param {string} message - The message to display inside the toast.
 * @param {number} duration - The duration (in milliseconds) for which the toast should be visible (default: 2000ms).
 */
function showToast(type, message, duration = 2000) {
    let toastSelector = type === "success" ? "#toastSuccess" : "#toastError"; // Select the appropriate toast container
    let messageSelector = type === "success" ? "#toastSuccessMessage" : "#toastErrorMessage"; // Select the message span

    $(messageSelector).text(message); // Set the toast message dynamically
    let $toast = $(toastSelector); // Select the toast element using jQuery

    // Create a Bootstrap Toast instance with a custom delay (duration)
    let toast = new bootstrap.Toast($toast[0], { delay: duration });

    toast.show(); // Display the toast
}

/**
 * Tags a document with multiple tag names.
 * @param {number} docId - The ID of the document.
 * @param {string[]} tagNames - An array of tag names to be assigned.
 */
async function tagDocument(docId, tagNames) {
    try {
        console.log(`Tagging document ${docId} with tags: '${tagNames.join(", ")}'...`);

        // Send a POST request to assign multiple tags to the document
        const response = await $.ajax({
            url: '/api/tag_document', // API endpoint for tagging
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ doc_id: docId, tag_names: tagNames }) // Send document ID and tag names as an array
        });

        console.log("Document tagged successfully:", response); // Log success response
        showToast("success", `Document successfully tagged with: '${tagNames.join(", ")}'.`);
        loadInboxList(); // Reload inbox list to reflect changes
    } catch (error) {
        console.error("Error tagging document:", error); // Log error
        showToast("error", "Error tagging document.");
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
        const btnNextTags = $("#btnNext").data("tags").split(",");
        const btnSendToAITags = $("#btnSendToAI").data("tags").split(",");
        const btnInvestigateTags = $("#btnInvestigate").data("tags").split(",");

        $("#btnNext").on("click", function() {
            tagDocument(docId, btnNextTags);
        });

        $("#btnSendToAI").on("click", function() {
            tagDocument(docId, btnSendToAITags);
        });

        $("#btnInvestigate").on("click", function() {
            tagDocument(docId, btnInvestigateTags);
        });

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
        showToast("error", "Error loading document");
    }
}

/**
 * Initializes event listeners on page load.
 * - Handles sidebar toggle
 * - Binds the refresh metadata button
 * - Adjusts the PDF viewer height on window resize
 */
$(document).ready(function () {
    $(window).on('resize', updatePdfImageHeight);
    loadInboxList();

    // Sidebar toggle functionality
    $("#sidebarToggle").on("click", function () {
        $("#sidebar, #content").toggleClass("collapsed");
    });

    // Refresh metadata button functionality
    $("#navRefresh").on("click", async function (event) {
        event.preventDefault();
        try {
            const response = await fetch("/refreshMetadata");
            if (!response.ok) throw new Error(`Error refreshing metadata: ${response.statusText}`);
            console.log("Metadata successfully refreshed!");
            showToast("success", "Metadata successfully refreshed.");
        } catch (error) {
            console.error("Error refreshing metadata:", error);
            showToast("error", "Error refreshing metadata.");
        }
    });
});