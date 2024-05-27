// Get references to the input fields
const startingYearInput = document.getElementById('starting_year');
const endingYearInput = document.getElementById('ending_year');

// Event listener for starting year input
startingYearInput.addEventListener('input', function () {
    const startingYear = parseInt(startingYearInput.value);
    if (!isNaN(startingYear)) {
        endingYearInput.value = (startingYear + 1).toString();
    }
});
// Event listener for ending year input
endingYearInput.addEventListener('input', function () {
    const endingYear = parseInt(endingYearInput.value);
    if (!isNaN(endingYear)) {
        startingYearInput.value = (endingYear - 1).toString();
    }
});

function addRows(count) {
    var table = document.getElementById('studentList');
    var tbody = table.getElementsByTagName('tbody')[0]; // Get the tbody element

    for (var i = 0; i < count; i++) {
        var row = tbody.insertRow(-1) // Insert a new row at the end of the table
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        var cell3 = row.insertCell(2);
        var cell4 = row.insertCell(3);
        var cell5 = row.insertCell(4);
        var cell6 = row.insertCell(5);

        cell1.innerHTML = `<div class="my-2 text-center" ><input type="checkbox" class="checkbox" id="${i}"></div>`;
        cell2.innerHTML = `<input type="text" class="form-control w-full text-truncate" id="student_surname" name="student_surname" placeholder = ""> `; // Last Name
        cell3.innerHTML = `<input type="text" class="form-control w-full text-truncate" id="student_firstname" name="student_firstname" placeholder = ""> `; // First Name
        cell4.innerHTML = `<input type="text" class="form-control text-truncate text-center" id="student_middlename" name="student_middlename" maxlength="2" pattern="[a-zA-Z]{1}\.?" placeholder = ""> `; // MI
        cell5.innerHTML = `<input type="text" class="form-control text-truncate text-center" id="student_suffixname" name="student_suffixname" maxlength="4" placeholder = ""> `; // Suffix
        cell6.innerHTML = `<button class="text-center border-0" id="deleteButton${i}"><span class="fa-solid fa-square-minus"></span></button>`; // Button

        (function (row) {
            cell6.querySelector(`#deleteButton${i}`).addEventListener('click', function () {
                row.remove();
            });
        })(row);
    }
}

addRows(10);

//student list tools
function populateResults(students) {
    var table = document.getElementById('studentList');
    var tbody = table.getElementsByTagName('tbody')[0];
    clearEmptyRows();

    if (students.length > 0) {
        students.forEach(function (student, index) {
            var isDuplicate = false;
            tbody.querySelectorAll('tr').forEach(function (row) {
                var surname = row.querySelector('[name="student_surname"]').value;
                var firstname = row.querySelector('[name="student_firstname"]').value;
                var middlename = row.querySelector('[name="student_middlename"]').value;
                var suffixname = row.querySelector('[name="student_suffixname"]').value;
                if (surname === student.surname &&
                    firstname === student.firstname &&
                    middlename === student.middlename &&
                    suffixname === student.suffix) {
                    isDuplicate = true;
                    return;
                }
            });

            if (!isDuplicate) {
                var row = tbody.insertRow(-1); // Insert a new row at the end of the table

                var cell1 = row.insertCell(0);
                var cell2 = row.insertCell(1);
                var cell3 = row.insertCell(2);
                var cell4 = row.insertCell(3);
                var cell5 = row.insertCell(4);
                var cell6 = row.insertCell(5);

                cell1.innerHTML = `<div class="my-2 text-center"><input type="checkbox" class="checkbox" id="${index}"></div>`;
                cell2.innerHTML = `<input type="text" class="form-control w-full text-truncate" id="student_surname" name="student_surname" value="${student.surname}" placeholder="">`; // Last Name
                cell3.innerHTML = `<input type="text" class="form-control w-full text-truncate" id="student_firstname" name="student_firstname" value="${student.firstname}" placeholder="">`; // First Name
                cell4.innerHTML = `<input type="text" class="form-control text-truncate text-center" id="student_middlename" name="student_middlename" maxlength="2" value="${student.middlename}" pattern="[a-zA-Z]{1}\.?" placeholder="">`; // MI
                cell5.innerHTML = `<input type="text" class="form-control text-truncate text-center" id="student_suffixname" name="student_suffixname" maxlength="4" value="${student.suffix}" placeholder="">`; // Suffix
                cell6.innerHTML = `<button class="px-2 border-0" id="deleteButton${index}"><span class="fa-solid fa-square-minus"></span></button>`; // Button

                cell6.querySelector(`#deleteButton${index}`).addEventListener('click', function () {
                    row.remove();
                });
            }
        });
    }
}



function clearEmptyRows() {
    var table = document.getElementById('studentList');
    var tbody = table.getElementsByTagName('tbody')[0];
    var rows = tbody.getElementsByTagName('tr');

    // Iterate over the rows in reverse order
    for (var i = rows.length - 1; i >= 0; i--) {
        var row = rows[i];
        let surnameInput = row.querySelector('input[name="student_surname"]');
        let firstnameInput = row.querySelector('input[name="student_firstname"]');

        // Check if both surname and firstname are empty
        if (surnameInput.value.trim() === "" || firstnameInput.value.trim() === "") {
            // Delete the row
            row.remove();
        }
    }
}

document.querySelector('#removeButton').addEventListener('click', handleRemoveOrClear);
document.querySelector('#clearButton').addEventListener('click', handleRemoveOrClear);
function noSelectedData(event, message, buttonFunction) {
    let messageErrorTools = document.getElementById('errorContainerTools');
    messageErrorTools.innerHTML = ''; // Clear any existing content

    messageErrorTools.innerHTML = `
        <div class="modal-body">
            <div>
                <h5 class="fw-bold mb-3"> No selected data to run ${event} function</h5>
                <p>${message}</p>
            </div>
        </div>
        <div class="modal-footer">
            <button type="button" data-bs-dismiss="modal" class="button">Cancel</button>
            <button id="${buttonFunction}" class="btn-red fw-bold text-decoration-none button" data-bs-dismiss="modal">
                Confirm
            </button>
        </div>
    `;

    $('#selection_uploadTools').modal('show'); // Show the modal
}

function handleRemoveOrClear(event) {
    var checkboxes = document.querySelectorAll('tbody .checkbox:checked');
    var selectAll = document.querySelector('#select-all');

    if (checkboxes.length === 0) {
        if (event.target.id === 'removeButton') {
            $('#deleteSelctedList_confirmation').modal('hide');
            noSelectedData('remove', 'Remove all rows instead?', 'removeAllRows');
        } else if (event.target.id === 'clearButton') {
            $('#clearSelctedList_confirmation').modal('hide');
            noSelectedData('clear', 'Clear all rows instead?', 'clearAllRows');
        }
    } else {
        checkboxes.forEach(function (checkbox) {
            var row = checkbox.closest('tr');
            var inputFields = row.querySelectorAll('input[type="text"]');

            if (event.target.id === 'removeButton') {
                row.remove();
                showToast('Success!', 'Removed rows successfully.', 'fc-green fa-solid fa-circle-check', 'border-success');
                new bootstrap.Toast(document.querySelector('#add_userToast')).show();
            } else if (event.target.id === 'clearButton') {
                inputFields.forEach(function (input) {
                    input.value = '';
                });
                showToast('Success!', 'Cleared rows input fields successfully.', 'fc-green fa-solid fa-circle-check', 'border-success');
                new bootstrap.Toast(document.querySelector('#add_userToast')).show();
            }
        });
    }

    selectAll.checked = false;
    var tbodyIsEmpty = document.querySelector('tbody').childElementCount === 0;
    if (tbodyIsEmpty) {
        addRows(10);
    }
}

function handleRemoveOrClear_allData(event) {
    var rows = document.querySelectorAll('tbody tr'); // Get all rows
    var inputFields = document.querySelectorAll('tbody input[type="text"]'); // Get all input fields

    if (event.target.id === 'removeAllRows') {
        rows.forEach(function (row) {
            row.remove(); // Remove all rows
        });
        addRows(10);
        showToast('Success!', 'Removed rows successfully.', 'fc-green fa-solid fa-circle-check', 'border-success');
        new bootstrap.Toast(document.querySelector('#add_userToast')).show();
    } else if (event.target.id === 'clearAllRows') {
        inputFields.forEach(function (input) {
            input.value = ''; // Clear input fields
        });
        showToast('Success!', 'Cleared rows input fields successfully.', 'fc-green fa-solid fa-circle-check', 'border-success');
        new bootstrap.Toast(document.querySelector('#add_userToast')).show();
    }
}

// Event listener for the "Select All" checkbox
document.querySelector('#select-all').addEventListener('change', function () {
    var checkboxes = document.querySelectorAll('.checkbox');

    // If "Select All" checkbox is checked, check all other checkboxes
    if (this.checked) {
        checkboxes.forEach(function (checkbox) {
            checkbox.checked = true;
        });
    } else {
        // If "Select All" checkbox is unchecked, uncheck all other checkboxes
        checkboxes.forEach(function (checkbox) {
            checkbox.checked = false;
        });
    }
});

// Event listener for individual checkboxes
document.querySelectorAll('tbody .checkbox').forEach(function (checkbox) {
    checkbox.addEventListener('change', function () {
        // If any individual checkbox is unchecked, uncheck the "Select All" checkbox
        var selectAllCheckbox = document.querySelector('#select-all');
        if (!this.checked) {
            selectAllCheckbox.checked = false;
        }

        var allCheckboxes = document.querySelectorAll('tbody .checkbox');
        var allChecked = Array.from(allCheckboxes).every(function (checkbox) {
            return checkbox.checked;
        });

        document.querySelector('#select-all').checked = allChecked;
    });
});

