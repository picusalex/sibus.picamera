

function populateArchiveTable(archive_path=undefined) {
	var root_url = "http://rasp-car:5000/archives";
	if (archive_path === undefined) {
		archive_path = root_url;
	}
	
	console.log("Fetching data from: "+archive_path);
	
	$.getJSON(archive_path, function(data) {
		console.log("Call success ! "+data);
		
		$("#folder_table_view").empty()
		
		if (archive_path != root_url) {
			var s = archive_path.substring(0, archive_path.lastIndexOf('/'));
			
			
			var tr = $("<tr>");
			tr.attr("path", archive_path.substring(0, archive_path.lastIndexOf('/')) )
			tr.click(function() {
				var path = $(this).attr("path");
				populateArchiveTable(path);
			});
			
			tr.append("<td><i class=\"glyphicon glyphicon-circle-arrow-left\"></i><td>UP</td><td></td><td></td>");
			
			$("#folder_table_view").append(tr);
		}
		
		data.dirs.forEach(function(element) {
			var tr = $("<tr>");
			tr.attr("path", archive_path+"/"+element)
			tr.click(function() {
				var path = $(this).attr("path");
				populateArchiveTable(path);
			});
			
			tr.append("<td><i class=\"glyphicon glyphicon-folder-close\"></i><td>"+element+"</td><td>-</td><td>-</td>");
			
			$("#folder_table_view").append(tr);
		});
		
		data.files.forEach(function(element) {
			var tr = $("<tr>");
			tr.attr("path", archive_path+"/"+element)
			tr.click(function() {
				var path = $(this).attr("path");
				populatePictureView(path);
			});
			
			tr.append("<td><i class=\"glyphicon glyphicon-picture\"></i><td>"+element+"</td><td>-</td><td>-</td>");
			
			$("#folder_table_view").append(tr);			
			
		});
		
		$("#folder_table_view").attr("cur_path", archive_path);	
	});
	
}

function populatePictureView(picture_path) {
	$("#picture_view").attr("src", picture_path) ;	
}
