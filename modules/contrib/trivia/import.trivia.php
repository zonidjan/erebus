<?php
$db = json_decode(file_get_contents("modules/trivia.json"), TRUE);
$fh = fopen('qs.txt', 'r');
foreach (file('qs.txt') as $line) {
	list($q, $a) = explode('*', trim($line), 2);
	$db['questions'][] = array('question' => $q, 'answer' => trim($a));
}
file_put_contents('modules/trivia.json', json_encode($db));
