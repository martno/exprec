"use strict";


$(document).ready(function() {
    loadMain([], ['archive']);

    addTags();

    $('.button-archive').click(function() {
        if (getNumSelectedExperiments() == 0) {
            alert('Please select at least one experiment');
            return;
        }

        $('.experiment-row').each(function() {
            if ($(this).is(':checked')) {
                var checkboxId = $(this).attr('id');
                var id = checkboxId.replace('checkbox-', '');
                var _ = postJson('/add_tags/' + id, ["archive"]);
            }

            loadMain([], ['archive']);
        });
    });

    $('.button-delete').click(function() {
        if (getNumSelectedExperiments() == 0) {
            alert('Please select at least one experiment');
            return;
        }

        var doDelete = confirm("Do you want to delete all selected experiments?");

        if (doDelete == true) {
            $('.experiment-row').each(function() {
                if ($(this).is(':checked')) {
                    var checkboxId = $(this).attr('id');
                    var id = checkboxId.replace('checkbox-', '');
                    var _ = deleteRequest('/experiment/' + id);
                }

                loadMain([], ['archive']);
            });
        }
    });

    $('.button-delete-files').click(function() {
        if (getNumSelectedExperiments() == 0) {
            alert('Please select at least one experiment');
            return;
        }

        var doDeleteFiles = confirm("Do you want to delete all files associated with selected experiments?");

        if (doDeleteFiles == true) {
            $('.experiment-row').each(function() {
                if ($(this).is(':checked')) {
                    var checkboxId = $(this).attr('id');
                    var id = checkboxId.replace('checkbox-', '');
                    var _ = $.get('/deletefiles/' + id);
                }

                loadMain([], ['archive']);
            });
        }
    });

    $('.button-add-tags').click(function() {
        if (getNumSelectedExperiments() == 0) {
            alert('Please select at least one experiment');
            return;
        }

        var tags = prompt("Enter tags to add (separate by space)");
        tags = tags.split(" ");

        $('.experiment-row').each(function() {
            if ($(this).is(':checked')) {
                var checkboxId = $(this).attr('id');
                var id = checkboxId.replace('checkbox-', '');
                var _ = postJson('/add_tags/' + id, tags);
            }

            loadMain([], ['archive']);
        });
    });

    $('.button-remove-tags').click(function() {
        if (getNumSelectedExperiments() == 0) {
            alert('Please select at least one experiment');
            return;
        }

        var tags = prompt("Enter tags to remove (separate by space)");
        tags = tags.split(" ");

        $('.experiment-row').each(function() {
            if ($(this).is(':checked')) {
                var checkboxId = $(this).attr('id');
                var id = checkboxId.replace('checkbox-', '');
                var _ = postJson('/remove_tags/' + id, tags);
            }

            loadMain([], ['archive']);
        });
    });

    $('#show-inbox').click(function() {
        loadMain([], ['archive']);
    });

    $('#show-archive').click(function() {
        loadMain(['archive'], []);
    });

    $('[data-toggle="tooltip"]').tooltip();

    $('.button-compare').click(function() {
        var checked = [];

        $('.experiment-row').each(function() {
            if ($(this).is(':checked')) {
                var checkboxId = $(this).attr('id');
                var id = checkboxId.replace('checkbox-', '');
                checked.push(id);
            }
        });

        if (checked.length == 1 || checked.length == 2) {
            var promise;
            if (checked.length == 1) {
                var uuid = checked[0];
                promise = $.get('/compare-with-local/' + uuid);
            } else {
                promise = postJson('/compare-experiments', checked);
            }

            promise.done(function(result) {
                var html = result["html"];
                var diffString = result["diffString"];

                $('#experiments-div').html(html);
                $('#main').hide();
                $('.button-go-back').click(function() {
                    $('#main').show();
                    $('#experiments-div').html('');
                });

                var diff2htmlUi = new Diff2HtmlUI({diff: diffString});
                diff2htmlUi.draw('#diff-div', {inputFormat: 'diff', showFiles: true, matching: 'lines'});
                diff2htmlUi.highlightCode('#diff-div');
            });
        } else {
            alert("Select one or two experiments to compare.");
        }
    });
});


function getNumSelectedExperiments() {
    var numSelected = 0;
    $('.experiment-row').each(function() {
        if ($(this).is(':checked')) {
            numSelected += 1;
        }
    });

    return numSelected;
}


function deleteRequest(url) {
    return $.ajax({
        url: url,
        type: 'DELETE',
    });
}


function loadMain(whitelist, blacklist) {
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
            });
        });

        var table = $('#experiment-table').DataTable({
            dom: 'Bfrtip',
            stateSave: true,
            buttons: [
                'columnsToggle'
            ],
            "order": [[ 7, "desc" ]]  // 'Start' column
        });
    });
}


function addTags() {
    $.get('/alltags', function(tags) {
        for (let tag of tags) {
            var tag_html = '<button type="button" class="btn btn-link btn-sm text-left" style="width: 120px;" id="tag-' + tag + '">' + tag + '</button><br>';
            $('#tag-buttons').append(tag_html);

            $('#tag-' + tag).click(function() {
                loadMain([tag], ['archive']);
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

