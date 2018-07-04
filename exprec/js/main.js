"use strict";

var UUID_INDEX = 1;


$(document).ready(function() {
    loadMain([], ['archive']);

    addTags();

    $('.button-archive').click(function() {
        var selectedUuids = getSelectedUuids();
        if (selectedUuids == 0) {
            alert('Please select at least one experiment');
            return;
        }

        for (let uuid of selectedUuids) {
            var _ = postJson('/add_tags/' + uuid, ["archive"]);
        }
        loadMain([], ['archive']);
    });

    $('.button-delete').click(function() {
        var selectedUuids = getSelectedUuids();
        if (selectedUuids == 0) {
            alert('Please select at least one experiment');
            return;
        }

        var doDelete = confirm("Do you want to delete all selected experiments?");

        if (doDelete == true) {
            for (let uuid of selectedUuids) {
                var _ = deleteRequest('/experiment/' + uuid);
            }
            loadMain([], ['archive']);
        }
    });

    $('.button-delete-files').click(function() {
        var selectedUuids = getSelectedUuids();
        if (selectedUuids == 0) {
            alert('Please select at least one experiment');
            return;
        }

        var doDeleteFiles = confirm("Do you want to delete all files associated with selected experiments?");

        if (doDeleteFiles == true) {
            for (let uuid of selectedUuids) {
                var _ = $.get('/deletefiles/' + uuid);
            }
            loadMain([], ['archive']);
        }
    });

    $('.button-add-tags').click(function() {
        var selectedUuids = getSelectedUuids();
        if (selectedUuids == 0) {
            alert('Please select at least one experiment');
            return;
        }

        var tags = prompt("Enter tags to add (separate by space)");
        tags = tags.split(" ");

        for (let uuid of selectedUuids) {
            var _ = postJson('/add_tags/' + uuid, tags);
        }
        loadMain([], ['archive']);
    });

    $('.button-remove-tags').click(function() {
        var selectedUuids = getSelectedUuids();
        if (selectedUuids == 0) {
            alert('Please select at least one experiment');
            return;
        }

        var tags = prompt("Enter tags to remove (separate by space)");
        tags = tags.split(" ");

        for (let uuid of selectedUuids) {
            var _ = postJson('/remove_tags/' + uuid, tags);
        }
        loadMain([], ['archive']);
    });

    $('#show-inbox').click(function() {
        loadMain([], ['archive']);
        $('.button-go-back').click();
    });

    $('#show-archive').click(function() {
        loadMain(['archive'], []);
        $('.button-go-back').click();
    });

    $('[data-toggle="tooltip"]').tooltip();

    $('.button-compare').click(function() {
        var selectedUuids = getSelectedUuids();
        if (selectedUuids == 0) {
            alert('Please select at least one experiment');
            return;
        }

        var checked = [];

        var promise = postJson('/compare-experiments', selectedUuids);

        promise.done(function(result) {
            var html = result["html"];
            var diffString = result["diffString"];

            $('#experiments-div').html(html);
            $('#main').hide();
            $('.button-go-back').click(function() {
                $('#main').show();
                $('#experiments-div').html('');
            });
            
            if (diffString !== null) {
                var diff2htmlUi = new Diff2HtmlUI({diff: diffString});
                diff2htmlUi.draw('#diff-div', {inputFormat: 'diff', showFiles: true, matching: 'lines', outputFormat: 'side-by-side'});
                diff2htmlUi.highlightCode('#diff-div');
            }
        });
    });

    $('.button-toggle').click(function() {
        var table = $('#experiment-table').DataTable();  // Obtains the existing datatable in #experiment-table.
        if (getSelectedUuids().length > 0) {
            table.rows().deselect();
        } else {
            table.rows().select();
        }
    });

    showdown.setOption('simplifiedAutoLink', true);
});


function getSelectedUuids() {
    var uuids = new Array();
    var table = $('#experiment-table').DataTable();  // Obtains the existing datatable in #experiment-table.
    var rowData = table.rows('.selected').data();

    for (var i=0; i<rowData.length; i++) {
        uuids.push(rowData[i][UUID_INDEX]);
    }
    return uuids;
}


function deleteRequest(url) {
    return $.ajax({
        url: url,
        type: 'DELETE',
    });
}


function loadMain(whitelist, blacklist) {
    $('#experiment-table-div').html('Loading...');

    var promise = postJson('/experiment-table', {
        'whitelist': whitelist,
        'blacklist': blacklist
    });

    promise.done(function(content) {
        $('#experiment-table-div').html(content);
        console.log('#experiment-table-div loaded!');

        $(".experiment-button").click(function() {
            var buttonId = $(this).attr('id');
            console.log(buttonId);

            var id = buttonId.replace('button-', '');

            $('#experiments-div').load('/experiment/' + id, function() {
                $('#main').hide();
                $('.button-go-back').click(function() {
                    $('#main').show();
                    $('#experiments-div').html('');
                });

                $('.button-restore-source-code').click(function() {
                    var doRestore = confirm("Do you want to restore the source code from experiment " + id + "?\nThis will overwrite all local code.");
                    if (doRestore == true) {
                        var promise = $.get('/restore-source-code/' + id);
                        promise.done(function() {
                            alert(id + ' restored');
                        });
                    }
                });

                highlightAllCode();

                $('[data-toggle="tooltip"]').tooltip()
            });
        });

        var table = $('#experiment-table').DataTable({
            dom: 'Blfrtip',
            stateSave: true,
            stateDuration: 60 * 60 * 24 * 7,
            buttons: [ {
                extend: 'columnsToggle',
                columns: '.toggle'
            } ],
            "order": [[ 11, "desc" ]],  // 'Start' column
            columnDefs: [
                {
                    targets: 'hidden-title',
                    sortable: false,
                    searchable: false,
                    width: "0px",
                    title: " "
                },
                {
                    targets: 'hidden-column',
                    visible: false
                }
            ],
            select: {
                style: 'multi',
                selector: ':not(:first-child)'
            }
        });

        // Add event listener for opening and closing details
        $('#experiment-table').on('click', 'td.details-control', function() {
            var tr = $(this).closest('tr');
            var row = table.row( tr );
        
            if ( row.child.isShown() ) {
                row.child.hide();
                tr.removeClass('shown');
            }
            else {
                row.child( format(row.data()) ).show();
                tr.addClass('shown');
            }
        } );

        $('#experiment-table tbody').on( 'click', 'tr', function () {
            $(this).toggleClass('selected');
        } );
    });
}


function format ( d ) {
    // `d` is the original data object for the row
    return '<table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">'+
        '<tr>'+
            '<td>Title</td>'+
            '<td>'+ d[6] +'</td>'+
        '</tr>'+
        '<tr>'+
            '<td><i class="fas fa-info-circle"></i> Description:</td>'+
            '<td>'+ d[15] +'</td>'+
        '</tr>'+
        '<tr>'+
            '<td><i class="fas fa-lightbulb"></i> Conclusion:</td>'+
            '<td>'+ d[16] +'</td>'+
        '</tr>'+
        '<tr>'+
            '<td>Arguments:</td>'+
            '<td>'+ d[17] +'</td>'+
        '</tr>'+
        '<tr>'+
            '<td>Exception:</td>'+
            '<td>' + d[18] + '</td>'+
        '</tr>'+
    '</table>';
}


function addTags() {
    $.get('/alltags', function(tags) {
        for (let tag of tags) {
            var tag_html = '<button type="button" class="btn btn-link btn-sm text-left" style="width: 120px;" id="tag-' + tag + '">' + tag + '</button><br>';
            $('#tag-buttons').append(tag_html);

            $('#tag-' + tag).click(function() {
                loadMain([tag], ['archive']);
                $('.button-go-back').click();
            });
        }
    });
}


function highlightAllCode() {
    $('pre > code').each(function() {
        hljs.highlightBlock(this);
        hljs.lineNumbersBlock(this);
   });
}


function postJson(url, data) {
    var promise = $.ajax({
        type: "POST",
        url: url,
        data: JSON.stringify(data),
        contentType: 'application/json; charset=utf-8',
    });

    return promise;
}


function hasMethod(obj, method) {
    for (var id in obj) {
        if (typeof(obj[id]) == "function" && id === method) {
            return true;
        }
    }
    return false;
}


function getMethods(obj) {
    var result = [];
    for (var id in obj) {
      try {
        if (typeof(obj[id]) == "function") {
          result.push(id + ": " + obj[id].toString());
        }
      } catch (err) {
        result.push(id + ": inaccessible");
      }
    }
    return result;
}


function saveTitle(uuid) {
    var text = $('#titleTextInput').val();
    postJson("/save-text/" + uuid + '/title', text);
    $('#title-div').text(text);
}


function saveDescription(uuid) {
    var text = $('#descriptionTextArea').val();
    postJson("/save-text/" + uuid + '/description', text);

    var converter = new showdown.Converter();
    $('#description-div').html(converter.makeHtml(text));
}


function saveConclusion(uuid) {
    var text = $('#conclusionTextArea').val();
    postJson("/save-text/" + uuid + '/conclusion', text);

    var converter = new showdown.Converter();
    $('#conclusion-div').html(converter.makeHtml(text));
}


function copyToClipboard(text) {
    var $temp = $("<input>");
    $("body").append($temp);
    $temp.val(text).select();
    document.execCommand("copy");
    $temp.remove();
}
