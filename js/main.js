"use strict";


$( document ).ready(function() {
    loadMain([], ['archive']);

    addTags();

    $('.button-archive').click(function() {
        $('.experiment-row').each(function() {
            var atLeastOneArchived = false;

            if ($(this).is(':checked')) {
                var checkboxId = $(this).attr('id');
                var id = checkboxId.replace('checkbox-', '');
                var promise = postJson('/add_tags/' + id, ["archive"]);

                atLeastOneArchived = true;
            }

            if (atLeastOneArchived) {
                loadMain([], ['archive']);
            }
        });
    });

    $('#show-inbox').click(function() {
        loadMain([], ['archive']);
    });

    $('#show-archive').click(function() {
        loadMain(['archive'], []);
    });
});


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
                
                highlightAllCode();
            });
        });

        var table = $('#experiment-table').DataTable({
            dom: 'Bfrtip',
            stateSave: true,
            buttons: [
                'columnsToggle'
            ]
        });
    });
}


function addTags() {
    $.get('/alltags', function(tags) {
        for (let tag of tags) {
            var tag_html = '<button type="button" class="btn btn-link btn-sm text-left" style="width: 120px;" id="tag-' + tag + '">' + tag + '</button><br>';
            $('#tag-buttons').append(tag_html);

            $('#tag-' + tag).click(function() {
                loadMain([tag], []);
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

