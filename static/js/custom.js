// Adjusts the PDF image height based on the available window height
function updatePdfImageHeight() {
    const availableHeight = window.innerHeight - 80;
    $('#pdfImage').css("maxHeight", availableHeight + 'px');
}

// Loads the inbox list and initializes pagination
function loadInboxList() {
    $.getJSON('/doc/list_inbox')
        .done(function (inboxDict) {
            $("#pagination").empty();

            if (inboxDict.length > 0) {
                loadDocument(inboxDict[0]);
            } else {
                loadDocument(-1);
            }

            // Generate pagination links
            inboxDict.forEach((doc, index) => {
                let pageItem = $('<li class="page-item"></li>');
                let pageLink = $('<a class="page-link" href="#">' + (index + 1) + '</a>');

                pageLink.click(function (event) {
                    event.preventDefault();
                    loadDocument(doc);
                });

                pageItem.append(pageLink);
                $("#pagination").append(pageItem);
            });
        })
        .fail(function () {
            console.error("Error loading inbox list.");
            showToast("error", "Error loading inbox list.");
        });
}

// Displays a Bootstrap toast notification
function showToast(type, message, duration = 2000) {
    let toastSelector = type === "success" ? "#toastSuccess" : "#toastError";
    let messageSelector = type === "success" ? "#toastSuccessMessage" : "#toastErrorMessage";

    $(messageSelector).text(message);
    let toast = new bootstrap.Toast($(toastSelector)[0], { delay: duration });
    toast.show();
}

/**
 * Sends a request to tag a document with the specified tags.
 *
 * @param {number} docId - The ID of the document to be tagged.
 * @param {Array} tags - An array of tag names to assign to the document.
 */
async function tagDocument(docId, tags) {
    try {
        if (!docId || tags.length === 0) {
            console.warn("tagDocument called with invalid parameters:", docId, tags);
            return;
        }

        console.log(`Tagging document ${docId} with tags:`, tags);

        const response = await fetch(`/doc/set_tag/${docId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tags }),
        });

        if (!response.ok) throw new Error(`Failed to tag document: ${response.statusText}`);

        showToast("success", "Document tagged successfully.");
        loadInboxList();  // Reloads inbox to reflect changes
    } catch (error) {
        console.error("Error tagging document:", error);
        showToast("error", "Error tagging document.");
    }
}

// Loads both document information and the corresponding PDF preview
async function loadDocument(docId) {
    try {
        if (docId === -1) {
            $('#title, #cor, #type, #path').text("");
            $('#tags').empty();

            $('#pdf-container').empty().html('<div class="d-flex justify-content-center align-items-center" style="height: 400px;"><div class="text-center"><span class="text-danger" style="font-size: 100px;">&#10060;</span><p class="text-danger fw-bold mt-2" style="font-size: 18px;">No Documents to process</p></div></div>');
            return;
        }

        const infoResponse = await $.getJSON(`/doc/get_info/${docId}`);

        $('#title').text(infoResponse.title);
        $('#cor').text(infoResponse.correspondent);
        $('#type').text(infoResponse.type);
        $('#path').text(infoResponse.storage_path);

        const tagsContainer = $('#tags').empty();
        infoResponse.tags.forEach(tag => {
            tagsContainer.append($('<span></span>').addClass('badge rounded-pill bg-danger me-1').text(tag));
        });

        // Button click event handlers
        //$("#btnNext").off("click").on("click", () => tagDocument(docId, $("#btnNext").data("tags").split(",")));
        //$("#btnSendToAI").off("click").on("click", () => tagDocument(docId, $("#btnSendToAI").data("tags").split(",")));
        //$("#btnInvestigate").off("click").on("click", () => tagDocument(docId, $("#btnInvestigate").data("tags").split(",")));
        $("#btnNext").off("click").on("click", function () {
            const tags = $(this).attr("data-tags") || "";
            tagDocument(docId, tags.split(","));
        });
        
        $("#btnSendToAI").off("click").on("click", function () {
            const tags = $(this).attr("data-tags") || "";
            tagDocument(docId, tags.split(","));
        });
        
        $("#btnInvestigate").off("click").on("click", function () {
            const tags = $(this).attr("data-tags") || "";
            tagDocument(docId, tags.split(","));
        });

        // Load and display the PDF preview
        const pdfImage = $('#pdfImage').hide();
        const placeholder = $('#pdf-placeholder').addClass('d-flex').show();

        if (infoResponse.thumbnail_url) {
            pdfImage.attr('src', infoResponse.thumbnail_url).off('load error').on({
                'load': function () {
                    placeholder.hide().css({
                        "display": "none!important",
                        "visibility": "hidden!important",
                        "opacity": "0",
                        "height": "0",
                        "width": "0"
                    });
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

// Initializes event listeners on page load
$(document).ready(function () {
    $(window).on('resize', updatePdfImageHeight);
    loadInboxList();

    $("#sidebarToggle").on("click", function () {
        $("#sidebar, #content").toggleClass("collapsed");
    });

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
