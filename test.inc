<?php

// PHP-Informationen anzeigen
phpinfo();

// Bilder im Verzeichnis anzeigen
function listFiles($dir){
    $files = scandir($dir);

    foreach($files as $file){
        if(is_dir($dir."/".$file) && $file != "." && $file != ".."){
            listFiles($dir."/".$file);
        } else {
            $extension = pathinfo($dir."/".$file, PATHINFO_EXTENSION);
            if(in_array($extension, ["jpeg", "jpg", "png", "gif", "svg"])) {
                echo $dir."/".$file."<br>";
            }
        }
    }
}

echo "<h2>Image files:</h2>";
listFiles(".");
?>