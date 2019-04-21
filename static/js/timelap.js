var filelist = undefined;

function populateTimeLap(camera) {
    if (camera === null) {
        console.log("ERROR: no camera name provided !");
        return;
    }
    
    var archive_path = "http://rasp-car:5000/archives";
    var timelap_path = "http://rasp-car:5000/timelap/"+camera;
	
	console.log("Fetching data from: "+timelap_path);
	
	$.getJSON(timelap_path, function(data) {
		console.log("Call success ! "+data);
		
		$("#folder_table_view").empty()
						
		if (data.files.length > 0) {
			filelist = data.files;
			
			$("#sliderImage").attr("max", filelist.length);
			$("#sliderImage").attr("value", filelist.length);
			var picture_path = archive_path+"/"+filelist[0];
			populatePictureView(picture_path);
			
			$("#sliderImage").on("input change", function( event, ui ) {
				var idx = filelist.length - $(this).val();
				var picture_path = archive_path+"/"+filelist[idx];
				populatePictureView(picture_path);
				
			});
		}
		
		$("#folder_table_view").attr("cur_path", archive_path);	
	});
	
}

function populatePictureView(picture_path) {
	$("#picture_view").attr("src", picture_path) ;	
}
