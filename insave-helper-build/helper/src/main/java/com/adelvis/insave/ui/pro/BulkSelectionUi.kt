package com.adelvis.insave.ui.pro

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

data class SelectedMedia(
    val id: String,
    val title: String,
    val url: String,
    val thumbnailUrl: String?,
    val uploader: String?,
    val durationSeconds: Int,
)

object BulkSelectionState {
    private val selected = mutableStateListOf<SelectedMedia>()
    private var expanded by mutableStateOf(false)
    private val visible = LinkedHashMap<String, SelectedMedia>()

    @JvmStatic fun visibleLimit(): Int = if (expanded) 30 else 6
    @JvmStatic fun isExpanded(): Boolean = expanded
    @JvmStatic fun selectedCount(): Int = selected.size
    @JvmStatic fun visibleCount(): Int = visible.size
    @JvmStatic fun selectedSnapshot(): List<SelectedMedia> = selected.toList()

    @JvmStatic fun beginVisiblePass() { visible.clear() }
    @JvmStatic fun registerVisible(item: SelectedMedia) { visible[item.id] = item }
    @JvmStatic fun isSelected(id: String): Boolean = selected.any { it.id == id }

    @JvmStatic fun toggle(item: SelectedMedia) {
        val index = selected.indexOfFirst { it.id == item.id }
        if (index >= 0) selected.removeAt(index) else selected.add(item)
    }

    @JvmStatic fun selectVisible() {
        visible.values.forEach { item ->
            if (selected.none { it.id == item.id }) selected.add(item)
        }
    }

    @JvmStatic fun clear() { selected.clear() }

    @JvmStatic fun clearForNewSearch() {
        selected.clear()
        visible.clear()
        expanded = false
    }

    @JvmStatic fun toggleExpanded() { expanded = !expanded }
}

@Composable
fun SelectionCheckbox(
    id: String,
    title: String,
    url: String,
    thumbnailUrl: String?,
    uploader: String?,
    durationSeconds: Int,
) {
    val item = SelectedMedia(id, title, url, thumbnailUrl, uploader, durationSeconds)
    BulkSelectionState.registerVisible(item)
    val checked = BulkSelectionState.isSelected(id)
    Checkbox(checked = checked, onCheckedChange = { BulkSelectionState.toggle(item) })
}

/**
 * ABI-simple version used by the recovered historical APK. Keeping only three
 * business arguments lets the smali call fit in a normal invoke-static without
 * perturbing Compose's large register frame. Thumbnail/uploader/duration are
 * optional metadata for queueing and are intentionally nullable/defaulted.
 */
@Composable
fun SelectionCheckboxCompact(
    id: String,
    title: String,
    url: String,
) {
    val item = SelectedMedia(id, title, url, null, null, 0)
    BulkSelectionState.registerVisible(item)
    val checked = BulkSelectionState.isSelected(id)
    Checkbox(checked = checked, onCheckedChange = { BulkSelectionState.toggle(item) })
}

@Composable
fun SearchSelectionFooter(
    totalCount: Int,
    onDownloadMp3: () -> Unit,
    onDownloadMp4: () -> Unit,
) {
    val selectedCount = BulkSelectionState.selectedCount()
    val expanded = BulkSelectionState.isExpanded()
    val visibleCount = BulkSelectionState.visibleCount()

    Column(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text(
                text = "Mostrando $visibleCount de $totalCount",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (totalCount > 6) {
                TextButton(onClick = { BulkSelectionState.toggleExpanded() }) {
                    Text(if (expanded) "⌃ Ver menos" else "⌄ Ver más")
                }
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            TextButton(onClick = { BulkSelectionState.selectVisible() }) {
                Text("Seleccionar visibles")
            }
            if (selectedCount > 0) {
                TextButton(onClick = { BulkSelectionState.clear() }) {
                    Text("Limpiar ($selectedCount)")
                }
            }
        }

        if (selectedCount > 0) {
            Text(
                text = "$selectedCount seleccionada(s)",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Button(modifier = Modifier.weight(1f), onClick = onDownloadMp3) { Text("MP3 256") }
                OutlinedButton(modifier = Modifier.weight(1f), onClick = onDownloadMp4) { Text("MP4 1080p") }
            }
        }
    }
}
