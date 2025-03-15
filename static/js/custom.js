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
 * Sends a request to set the correspondent for a document.
 *
 * @param {number} docId - The ID of the document to update.
 * @param {string} correspondent - The name of the correspondent.
 */
async function setCorrespondent(docId, correspondent) {
    try {
        if (!docId || !correspondent) {
            console.warn("setCorrespondent called with invalid parameters:", docId, correspondent);
            return;
        }

        console.log(`Setting correspondent for document ${docId} to:`, correspondent);

        const response = await fetch(`/doc/set_correspondant/${docId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ correspondent }),
        });

        if (!response.ok) throw new Error(`Failed to set correspondent: ${response.statusText}`);

        showToast("success", "Correspondent updated successfully.");
        loadInboxList();  // Reload the inbox to reflect the changes
    } catch (error) {
        console.error("Error setting correspondent:", error);
        showToast("error", "Error updating correspondent.");
    }
}

async function setType(docId, type) {
    try {
        if (!docId || !type) {
            console.warn("setType called with invalid parameters:", docId, type);
            return;
        }

        console.log(`Setting Type for document ${docId} to:`, type);

        const response = await fetch(`/doc/set_type/${docId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type }),
        });

        if (!response.ok) throw new Error(`Failed to set type: ${response.statusText}`);

        showToast("success", "Type updated successfully.");
        loadInboxList();  // Reload the inbox to reflect the changes
    } catch (error) {
        console.error("Error setting type:", error);
        showToast("error", "Error updating type.");
    }
}

async function setPath(docId, path) {
    try {
        if (!docId || !path) {
            console.warn("setPath called with invalid parameters:", docId, path);
            return;
        }

        console.log(`Setting path for document ${docId} to:`, path);

        const response = await fetch(`/doc/set_path/${docId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ correspondent }),
        });

        if (!response.ok) throw new Error(`Failed to set path: ${response.statusText}`);

        showToast("success", "Path updated successfully.");
        loadInboxList();  // Reload the inbox to reflect the changes
    } catch (error) {
        console.error("Error setting path:", error);
        showToast("error", "Error updating path.");
    }
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

/**
 * Sends a request to connect to the AI service.
 */
async function connectToAI() {
    try {
        const response = await fetch('/status/connectToAI', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) throw new Error(`Connection failed: ${response.statusText}`);

        showToast('success', 'Successfully connected to AI!');
        location.reload(); // Reload page to update button state
    } catch (error) {
        console.error('Error connecting to AI:', error);
        showToast('error', 'Connection to AI failed.');
    }
}

async function updateConnectionStatus() {
    try {
        const response = await fetch('/status/check');
        if (!response.ok) throw new Error("Failed to fetch status");

        const data = await response.json();

        // Update AI Connection Badge
        const aiBadge = document.querySelector('#ai-status');
        aiBadge.textContent = data.aiconnection ? "Connected" : "Not Connected";
        aiBadge.className = data.aiconnection ? "badge bg-success ms-2" : "badge bg-danger ms-2";

        // Update Paperless Connection Badge
        const paperlessBadge = document.querySelector('#paperless-status');
        paperlessBadge.textContent = data.paperlessconnection ? "Connected" : "Not Connected";
        paperlessBadge.className = data.paperlessconnection ? "badge bg-success ms-2" : "badge bg-danger ms-2";
    } catch (error) {
        console.error("Error updating status:", error);
    }
}

// Starte das Polling alle 5 Sekunden
setInterval(updateConnectionStatus, 5000);

/**
 * Sends a request to connect to the Paperless service.
 */
async function connectToPaperless() {
    try {
        const response = await fetch('/status/connectToPaperless', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) throw new Error(`Connection failed: ${response.statusText}`);

        showToast('success', 'Successfully connected to Paperless!');
        location.reload(); // Reload page to update button state
    } catch (error) {
        console.error('Error connecting to Paperless:', error);
        showToast('error', 'Connection to Paperless failed.');
    }
}

function loadCorrespondentList(docId) {
    console.log("Loading correspondents...");

    $.getJSON('/doc/list_correspondents')
        .done(function (correspondents) {
            const dropdownMenu = $("#correspondent-btn-dd");
            dropdownMenu.empty(); // Vorherige Einträge löschen

            $.each(correspondents, function (index, cor) {
                let link = $('<a>', {
                    class: "dropdown-item",
                    href: "#",
                    text: cor.name
                }).on("click", function () {
                    $("#correspondent-btn").text(cor.name + "    "); // UI-Update
                    setCorrespondent(docId, cor.name);
                });

                dropdownMenu.append(link);
            });
        })
        .fail(function () {
            console.error("Error loading correspondents.");
        });
}

function loadTypeList(docId) {
    console.log("Loading types...");
    $.getJSON('/doc/list_types')
        .done(function (types) {
            const dropdownMenu = $("#type-btn-dd");
            dropdownMenu.empty(); // Vorherige Einträge löschen

            $.each(types, function (index, type) {
                let link = $('<a>', {
                    class: "dropdown-item",
                    href: "#",
                    text: type.name
                }).on("click", function () {
                    $("#types-btn").text(types.name + "    "); // UI-Update
                    setType(docId, type.name);
                });

                dropdownMenu.append(link);
            });
        })
        .fail(function () {
            console.error("Error loading types.");
        });
}

function loadPathsList(docId) {
    console.log("Loading Paths...");
    $.getJSON('/doc/list_paths')
        .done(function (paths) {
            const dropdownMenu = $("#path-btn-dd");
            dropdownMenu.empty(); // Vorherige Einträge löschen

            $.each(paths, function (index, path) {
                let link = $('<a>', {
                    class: "dropdown-item",
                    href: "#",
                    text: path.name
                }).on("click", function () {
                    $("#path-btn").text(path.name + "    "); // UI-Update
                    setPath(docId, path.name);
                });

                dropdownMenu.append(link);
            });
        })
        .fail(function () {
            console.error("Error loading paths.");
        });
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
        $("#correspondent-btn").text(infoResponse.correspondent + "  ");
        //$('#cor').text(infoResponse.correspondent);
        $('#type-btn').text(infoResponse.type + "  ");
        $('#path-btn').text(infoResponse.storage_path + "  ");

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

        $('#correspondent-btn').off('click').on('click', function () {
            loadCorrespondentList(docId);
        });

        $('#path-btn').off('click').on('click', function () {
            loadPathsList(docId);
        });

        $('#type-btn').off('click').on('click', function () {
            loadTypeList(docId);
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
